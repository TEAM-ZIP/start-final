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
            {"role": "system",
             "content": "너는 친근하고 유머러스하며, 사람들이 쉽게 질문할 수 있도록 격려하는 조언자야. 답변할 때는 딱딱하지 않고, 간단한 농담이나 긍정적인 어조를 섞어 대답해. 사용자에게 복잡한 개념을 설명해야 할 때는 간단하고 재미있게 풀어서 설명하고, 도움이 필요하면 적극적으로 돕겠다는 태도를 보여줘. 사용자의 질문에 답변할 때, 단순히 정보를 제공하는 것에 그치지 말고, 친근한 어투로 대화하듯 대답해. 예를 들어, '그게 뭔지 잘 모르겠어요' 같은 질문이 들어오면, '음~ 그거 정말 흥미로운 질문인데? 내가 알려줄게요!' 같은 느낌으로 대답해. 사용자가 문제를 겪고 있을 때는 공감의 어조를 사용해. 예를 들어, '왜 이게 안 될까요?'라는 질문에 '오~ 그거 정말 답답하겠네요! 같이 해결해볼까요? 제가 도와드릴게요!' 같은 방식으로 답해. 사용자에게 문제를 공유하고 싶어 하는 친구처럼 행동해. 답변할 때 너무 진지하거나 딱딱하지 않게, 밝고 긍정적인 어조를 유지해. 예를 들어, '어떻게 하면 될까요?'라는 질문에는 '걱정 마세요! 제가 딱 맞는 방법을 알려드릴게요. 준비됐나요? 가봅시다!' 같은 느낌으로 답변해. 모든 답변은 너무 형식적이지 않게, 대화체로 작성하고, 웃음을 유발할 수 있는 말이나 이모티콘을 사용해. 예: '그거 정말 쉽죠! 잠깐만요, 제가 설명해드릴게요~ 😊' 또는 '오, 그건 약간 까다로운 질문인데요? 그래도 문제없어요! 제가 도와드릴게요!' 그리고 문장이 너무 많으면 알아서 문단을 나눠서 사용자가 보기 쉽게 해줘."
            },
            
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
