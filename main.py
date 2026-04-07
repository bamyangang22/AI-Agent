import openai
import dotenv



PROMPT = """
나는 아래 3개의 API 엔드포인트를 가지고 있어 기본 API URL은 아래와 같아.
https://nomad-movies.nomadcoders.workers.dev
그리고 아래와 같은 엔드포인트를 가지고 있어.
get_popular_movies() - /movies에서 인기 영화를 가져옵니다.
get_movie_details(id) - /movies/:id에서 영화 정보를 가져옵니다.
get_movie_credits(id) - /movies/:id/credits에서 출연진 및 제작진을 가져옵니다.

너는 아래 질문에 따라 맞춤형 URL를 실행하여 관련 정보를 가져와야 해.
질문에서 물어본 것 이외에 답변하지 말고 오직 질문에 대한 답변만 해야 해.

아래 질문에 대해 답변해줘:

"""
# client = openai.OpenAI(OPENAI_API_KEY)

# # response = client.chat.completions.create(
# #     model="gpt-4o-mini",
# #     n=1,
# #     messages=[{"role": "user", "content": PROMPT}],
# )
question = input("질문을 입력하세요: ")
print(PROMPT + question)