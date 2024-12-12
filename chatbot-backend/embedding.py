# 이미지도 같이 저장하는 버전
# 구글 드라이브에서 크롤링 한 파일 가져와서 라벨링 및 임베딩
import os
from google.oauth2.service_account import Credentials
from collections import defaultdict
from googleapiclient.discovery import build
from sentence_transformers import SentenceTransformer
import chromadb
import openai
from dotenv import load_dotenv
import base64

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = api_key

# Google Drive API 인증 설정
SERVICE_ACCOUNT_FILE = 'service_account.json'  # JSON 파일 경로
SCOPES = ['https://www.googleapis.com/auth/drive']

credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

# 공유 드라이브의 폴더 ID 설정 (공유 드라이브 URL에서 추출)
shared_folder_id = "1GwbcEfpaCbcbkhBpXjR4GOO6UFVjceiz"  # 실제 공유 드라이브 ID로 대체

# SentenceTransformer 및 ChromaDB 초기화
model = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient()

# 기존 컬렉션 삭제 후 생성
if "crawled_data" in [col.name for col in client.list_collections()]:
    client.delete_collection(name="crawled_data")
collection = client.create_collection(name="crawled_data")


# 라벨링 함수 수정
def label_topic(content):
    try:
        response = openai.chat.completions.create(
            messages=[
                {"role": "system", "content": "당신은 문서를 분석하여 적절한 주제를 할당하는 어시스턴트입니다. 가능한 주제는 '주거', '취업', '문화활동', '금융, 조례'입니다. 각 문서를 분석하여 관련이 높은 주제를 선택하세요. 하나만 선택하기 힘들다면 중복도 괜찮습니다."},
                {"role": "user", "content": f"다음 문서의 주제를 분석하고 적합한 주제를 단어로만 반환하세요:\n\n{content}"}
            ],
            model="gpt-4o",
        )
        label = response.choices[0].message.content
        print(f"주제 라벨링 결과: {label}")
        return label

    except Exception as e:
        print(f"라벨링 실패: {e}")
        return "기타"  # 실패 시 기본 라벨

# 지역 함수 수정
def label_region(content):
    try:
        response = openai.chat.completions.create(
            messages=[
                {"role": "system", "content": "당신은 문서를 분석하여 관련된 지역 정보를 파악하는 역할을 맡고 있습니다. 문서를 검토하여 해당 문서와 가장 관련이 있는 지역을 '시/군/구' 단위로 식별하세요. 결과는 '서울특별시 성동구'처럼 시와 구/군 이름이 포함된 전체 이름 형식으로 반환하세요. 만약 특정 지역과의 관련성이 없다면, '전국'이라는 값을 반환하세요."},
                {"role": "user", "content": f"다음 문서의 주제를 분석하고 적합한 지역을 단어로만 반환하세요:\n\n{content}"}
            ],
            model="gpt-4o",
        )
        region = response.choices[0].message.content
        print(f"지역 라벨링 결과: {region}")
        return region

    except Exception as e:
        print(f"지역 실패: {e}")
        return "기타"  # 실패 시 기본 라벨

# 모집 시작 날짜 라벨링 함수
def label_recruit_start_date(content):
    try:
        response = openai.chat.completions.create(
            messages=[
                {"role": "system", "content": (
                    "문서를 분석하여 모집 시작 날짜를 반환하세요. "
                    "결과는 반드시 아래 형식 중 하나를 따라야 합니다:\n\n"
                    "1. 'YYYY.MM.DD' 형식으로 날짜를 반환합니다. 예: '2024.01.15'\n"
                    "2. 모집 시작 날짜가 명시되지 않은 경우: '모집 시작 날짜 없음'\n"
                    "3. 문서에 모집과 관련된 내용이 없을 경우: '모집과 관련된 내용 없음'\n"
                    "4. 모집이 당일 시작된다는 경우: '오늘 모집 시작'\n\n"
                    "예시:\n"
                    "- 문서: '모집은 2024년 1월 15일부터 시작됩니다.'\n"
                    "  결과: '2024.01.15'\n"
                    "- 문서: '이 프로그램은 언제든지 지원 가능합니다.'\n"
                    "  결과: '모집 시작 날짜 없음'\n"
                    "- 문서: '이 프로그램은 오늘부터 시작됩니다.'\n"
                    "  결과: '오늘 모집 시작'\n"
                    "- 문서: '지원 절차는 없습니다.'\n"
                    "  결과: '모집과 관련된 내용 없음'\n"
                )},
                {"role": "user", "content": f"다음 문서를 분석하고 모집 시작 날짜를 반환하세요:\n\n{content}"}
            ],
            model="gpt-4o",
        )
        recruit_start_date = response.choices[0].message.content.strip()
        print(f"모집 시작 날짜 라벨링 결과: {recruit_start_date}")
        return recruit_start_date
    except Exception as e:
        print(f"모집 시작 날짜 라벨링 실패: {e}")
        return "모집 시작 날짜 없음"


# 모집 마감 날짜 라벨링 함수
def label_recruit_end_date(content):
    try:
        response = openai.chat.completions.create(
            messages=[
                {"role": "system", "content": (
                    "문서를 분석하여 모집 마감 날짜를 반환하세요. "
                    "결과는 반드시 아래 형식 중 하나를 따라야 합니다:\n\n"
                    "1. 'YYYY.MM.DD' 형식으로 날짜를 반환합니다. 예: '2024.01.31'\n"
                    "2. 모집 마감 날짜가 명시되지 않은 경우: '모집 마감 날짜 없음'\n"
                    "3. 문서에 모집과 관련된 내용이 없을 경우: '모집과 관련된 내용 없음'\n"
                    "4. 모집이 계속 진행된다는 경우: '모집 종료 없음'\n\n"
                    "예시:\n"
                    "- 문서: '모집은 2024년 1월 31일까지 진행됩니다.'\n"
                    "  결과: '2024.01.31'\n"
                    "- 문서: '모집 기간은 상시 진행됩니다.'\n"
                    "  결과: '모집 종료 없음'\n"
                    "- 문서: '모집 일정은 추후 공지됩니다.'\n"
                    "  결과: '모집 마감 날짜 없음'\n"
                    "- 문서: '이 프로그램은 지원 절차가 없습니다.'\n"
                    "  결과: '모집과 관련된 내용 없음'\n"
                )},
                {"role": "user", "content": f"다음 문서를 분석하고 모집 마감 날짜를 반환하세요:\n\n{content}"}
            ],
            model="gpt-4o",
        )
        recruit_end_date = response.choices[0].message.content.strip()
        print(f"모집 마감 날짜 라벨링 결과: {recruit_end_date}")
        return recruit_end_date
    except Exception as e:
        print(f"모집 마감 날짜 라벨링 실패: {e}")
        return "모집 마감 날짜 없음"

def label_implementation_start_date(content):
    try:
        response = openai.chat.completions.create(
            messages=[
                {"role": "system", "content": (
                    "문서를 분석하여 시행 시작 날짜를 반환하세요. "
                    "결과는 반드시 아래 형식 중 하나를 따라야 합니다:\n\n"
                    "1. 'YYYY.MM.DD' 형식으로 날짜를 반환합니다. 예: '2024.03.01'\n"
                    "2. 시행 시작 날짜가 명시되지 않은 경우: '시행 시작 날짜 없음'\n"
                    "3. 문서에 시행과 관련된 내용이 없을 경우: '시행과 관련된 내용 없음'\n"
                    "4. 시행이 오늘부터 시작된다는 경우: '오늘 시행 시작'\n\n"
                    "예시:\n"
                    "- 문서: '이 프로그램은 2024년 3월 1일부터 시행됩니다.'\n"
                    "  결과: '2024.03.01'\n"
                    "- 문서: '이 프로그램은 즉시 시작됩니다.'\n"
                    "  결과: '오늘 시행 시작'\n"
                    "- 문서: '시행 일정은 추후 결정됩니다.'\n"
                    "  결과: '시행 시작 날짜 없음'\n"
                    "- 문서: '시행 절차는 없습니다.'\n"
                    "  결과: '시행과 관련된 내용 없음'\n"
                )},
                {"role": "user", "content": f"다음 문서를 분석하고 시행 시작 날짜를 반환하세요:\n\n{content}"}
            ],
            model="gpt-4o",
        )
        implementation_start_date = response.choices[0].message.content.strip()
        print(f"시행 시작 날짜 라벨링 결과: {implementation_start_date}")
        return implementation_start_date
    except Exception as e:
        print(f"시행 시작 날짜 라벨링 실패: {e}")
        return "시행 시작 날짜 없음"


# 시행 마감 날짜 라벨링 함수
def label_implementation_end_date(content):
    try:
        response = openai.chat.completions.create(
            messages=[
                {"role": "system", "content": (
                    "문서를 분석하여 시행 마감 날짜를 반환하세요. "
                    "결과는 반드시 아래 형식 중 하나를 따라야 합니다:\n\n"
                    "1. 'YYYY.MM.DD' 형식으로 날짜를 반환합니다. 예: '2024.12.31'\n"
                    "2. 시행 마감 날짜가 명시되지 않은 경우: '시행 마감 날짜 없음'\n"
                    "3. 문서에 시행과 관련된 내용이 없을 경우: '시행과 관련된 내용 없음'\n"
                    "4. 시행이 계속 진행된다는 경우: '시행 종료 없음'\n\n"
                    "예시:\n"
                    "- 문서: '이 프로그램은 2024년 12월 31일까지 시행됩니다.'\n"
                    "  결과: '2024.12.31'\n"
                    "- 문서: '이 프로그램은 계속적으로 시행됩니다.'\n"
                    "  결과: '시행 종료 없음'\n"
                    "- 문서: '시행 일정은 추후 공지됩니다.'\n"
                    "  결과: '시행 마감 날짜 없음'\n"
                    "- 문서: '시행 절차는 없습니다.'\n"
                    "  결과: '시행과 관련된 내용 없음'\n"
                )},
                {"role": "user", "content": f"다음 문서를 분석하고 시행 마감 날짜를 반환하세요:\n\n{content}"}
            ],
            model="gpt-4o",
        )
        implementation_end_date = response.choices[0].message.content.strip()
        print(f"시행 마감 날짜 라벨링 결과: {implementation_end_date}")
        return implementation_end_date
    except Exception as e:
        print(f"시행 마감 날짜 라벨링 실패: {e}")
        return "시행 마감 날짜 없음"


# 이미지 분석 함수 수정
def analyze_image_base64(image_data, mime_type):
    try:
        # 이미지 데이터를 Base64로 인코딩
        image_base64 = base64.b64encode(image_data).decode("utf-8")
        # OpenAI API 호출
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "사진에 나와있는 정보(글들 위주로)를 설명해줘."},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{image_base64}"},
                        },
                    ],
                }
            ],
        )
        # 분석 결과 반환
        return response.choices[0].message.content.strip()
    except openai.error.OpenAIError as e:
        print(f"이미지 분석 중 오류 발생: {e}")
        return None



# # Google Drive에서 파일 가져오기
def get_files_by_prefix(folder_id, file_types=("text/plain", "image/jpeg", "image/png")):
    query = f"'{folder_id}' in parents"
    results = drive_service.files().list(q=query, fields="files(id, name, mimeType)").execute()
    return [file for file in results.get('files', []) if file["mimeType"] in file_types]


# Google Drive에서 파일 다운로드
def download_file(file_id):
    request = drive_service.files().get_media(fileId=file_id)
    return request.execute()


# 파일 그룹화
def group_files_by_prefix(files):
    grouped_files = defaultdict(list)
    for file in files:
        prefix = file["name"].split("_")[0] + "_" + file["name"].split("_")[1]
        grouped_files[prefix].append(file)
    return grouped_files

files = get_files_by_prefix(shared_folder_id)
if not files:
    print("Google Drive 폴더에서 파일을 찾을 수 없습니다.")
    grouped_files = {}  # 빈 딕셔너리로 초기화
else:
    grouped_files = group_files_by_prefix(files)



for prefix, file_group in grouped_files.items():
    text_content = None
    image_descriptions = []  # 이미지 분석 결과 리스트

    for file in file_group:
        mime_type = file["mimeType"]
        file_name = file["name"]

        if mime_type == "text/plain":
            text_content = download_file(file["id"]).decode("utf-8").strip()
            print(f"텍스트 파일 처리 완료: {file_name}")
        elif mime_type in ["image/jpeg", "image/png"]:
            # Google Drive에서 이미지 다운로드
            image_data = download_file(file["id"])
            # OpenAI Vision API로 이미지 분석
            image_description = analyze_image_base64(image_data, mime_type)
            if image_description:
                image_descriptions.append(image_description)
                print(f"이미지 분석 결과: {image_description}")

    if not text_content:
        print(f"그룹 '{prefix}'에 텍스트 파일이 없어 저장되지 않았습니다.")
        continue

    # 주제 라벨링
    label = label_topic(text_content)
    if not label:
        print(f"그룹 '{prefix}'의 주제 라벨 생성 실패로 저장되지 않았습니다.")
        continue
    print(f"그룹 '{prefix}'의 주제 라벨: {label}")

    # 지역 라벨링
    region = label_region(text_content)
    if not region:
        print(f"그룹 '{prefix}'의 지역 라벨 생성 실패로 저장되지 않았습니다.")
        continue
    print(f"그룹 '{prefix}'의 지역 라벨: {region}")

    # 모집 및 시행 날짜 라벨링
    recruit_start_date = label_recruit_start_date(text_content).strip().strip("'")
    recruit_end_date = label_recruit_end_date(text_content).strip().strip("'")
    implementation_start_date = label_implementation_start_date(text_content).strip().strip("'")
    implementation_end_date = label_implementation_end_date(text_content).strip().strip("'")
    
    print(f"그룹 '{prefix}'의 라벨링 결과:")
    print(f"  - 모집 시작: {recruit_start_date}")
    print(f"  - 모집 마감: {recruit_end_date}")
    print(f"  - 시행 시작: {implementation_start_date}")
    print(f"  - 시행 마감: {implementation_end_date}")

    # 임베딩 생성
    try:
        embedding = model.encode([text_content])[0]
    except Exception as e:
        print(f"임베딩 생성 실패: {e}")
        continue

    # 데이터 저장
    try:
        if image_descriptions:
            image_descriptions_str = "\n".join(image_descriptions)  # 리스트를 문자열로 합침
        else:
            image_descriptions_str = "이미지 분석 결과 없음"
        collection.add(
            documents=[text_content],
            embeddings=[embedding],
            metadatas=[
                {
                    "label": label,
                    "region": region,
                    "image_descriptions": image_descriptions_str,
                    "모집 시작": recruit_start_date,
                    "모집 마감": recruit_end_date,
                    "시행 시작": implementation_start_date,
                    "시행 마감": implementation_end_date,
                }
            ],
            ids=[prefix]
        )
        print(f"그룹 '{prefix}' 데이터를 성공적으로 저장했습니다.")
    except ValueError as e:
        print(f"데이터 저장 실패: {e}")