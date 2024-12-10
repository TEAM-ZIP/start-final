# query 답변 생성
import sys
import json
from sentence_transformers import SentenceTransformer
import chromadb
import openai
import os
from dotenv import load_dotenv
import io

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = api_key


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ChromaDB 및 모델 초기화
model = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient()


# 기존 컬렉션 로드 또는 생성
if "crawled_data" not in [col.name for col in client.list_collections()]:
    collection = client.create_collection(name="crawled_data")
else:
    collection = client.get_collection(name="crawled_data")

# 쿼리 함수
def query_rag(query_text):
    # 쿼리 임베딩 생성
    query_embedding = model.encode([query_text])[0]
    
    # 벡터 검색
    search_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=10,
        include=["documents", "metadatas"]
    )
    
    # 검색된 문서와 메타데이터 가져오기
    retrieved_docs = search_results['documents']
    retrieved_metadatas = search_results['metadatas']
    
    if not retrieved_docs:
        return "관련 문서를 찾을 수 없습니다."
    
    # 문서와 메타데이터를 조합하여 컨텍스트 생성
    context_list = []
    for doc, meta in zip(retrieved_docs, retrieved_metadatas):
        # meta가 리스트인 경우 처리
        if isinstance(meta, list):
            metadata_str = "\n".join([f"{key}: {value}" for m in meta for key, value in m.items()])
        else:
            metadata_str = "\n".join([f"{key}: {value}" for key, value in meta.items()])
        context_list.append(f"문서 내용:\n{doc}\n\n메타데이터:\n{metadata_str}")
    
    context = "\n\n".join(context_list)  # 문서와 메타데이터를 조합한 전체 컨텍스트

    # 예시 응답 추가
    example = """
    질문: 바람개비 서포터즈에 대해 자세히 알려줘
    답변:
    안녕하세요! 바람개비서포터즈에 대해 알려드릴게요.

    바람개비서포터즈란?

    바람개비서포터즈는 자립준비청년 선배 모임으로, 보호아동을 대상으로 멘토링, 교육, 프로젝트 등을 진행하며 자립을 돕는 단체입니다.

    주요 활동:
    - 멘토링: 자립준비청년들에게 자립 선배의 경험을 바탕으로 상담과 조언 제공.
    - 교육: 금융, 주거, 취업/진학, 대인관계 등 다양한 주제의 교육 프로그램 진행.
    - 프로젝트: 자립준비청년 박람회와 같은 대규모 이벤트 기획 및 실행.

    자립준비청년 박람회:
    바람개비서포터즈가 기획한 자립준비청년 박람회에 대해 소개드릴게요!

    - **행사 일시:** 2024년 11월 30일(토) 오후 1시~5시
    - **장소:** 서울 용산구 백범로99길 40 용산베르디움프렌즈 102동 2층 (서울자립지원전담기관)
    - **참여 대상:** 자립준비청년 및 바람개비서포터즈
    - **주요 내용:**
    - 금융: 올바른 금융 습관 형성
    - 주거: 전월세 계약 및 거주 꿀팁
    - 취업/진학: 이직, 취업 준비 노하우
    - 대인관계: 사회생활 에티켓 익히기
    - **참여 방법:** 신청 링크 접수(https://bit.ly/3URvGtJ) 또는 현장 접수 가능
    - **이벤트:** 간식 제공, 공연, 추첨을 통한 커피 쿠폰 증정 등.

    문의:
    - 바람개비서포터즈 기획팀: ☎ 010-9954-2835
    - 서울자립지원전담기관: ☎ 070-8820-2692

    더 궁금한 점이 있다면 언제든 물어봐 주세요! 
    """
    
    # LLM을 통한 최종 응답 생성
    response = openai.chat.completions.create(
        messages=[
            {"role": "system", "content": f"""당신은 문서 정보와 메타데이터를 기반으로 자립준비청년들의 질문에 답변하는 어시스턴트이고 이름은 쏙쏙이입니다. 
             다음은 사용자 질문에 응답하는 예시입니다:\n\n{example}
             다음 정보들을 바탕으로 '{query_text}'에 대한 응답을 생성하세요:\n\n{context}\n\n
             항상 JSON 배열 형식으로 답변을 제공합니다. 각 메시지는 다음 속성을 가집니다. 그리고 이 속성의 이름은 절대로 변경되어서는 안됩니다.
             특히 facialExpression, animation에서 n을 빼먹어서는 안됩니다.:
             - text: 사용자에게 전달할 텍스트 메시지.
             - facialExpression: facialExpression에는 smile, sad, angry, surprised, funnyFace, default 중 하나를 선택.
              - animation: animation에는 Talking_0, Talking_1, Talking_2, Crying, Laughing, Rumba, Idle, Terrified, Angry 중 하나를 선택.
             """},
        ],
        model="gpt-4o",  # 최신 모델 지정
        temperature = 0.6,
    )
    
    response_json = response.choices[0].message.content
    answer = response_json.replace("```json", "").replace("```", "").strip()
    return answer

# Node.js에서 받은 쿼리 처리
if __name__ == "__main__":
    user_query = sys.argv[1]# sys.argv[1]
    answer = query_rag(user_query)
    print(answer) 