from flask import Flask, render_template, jsonify, request
app = Flask(__name__)

from pymongo import MongoClient
client = MongoClient('localhost', 27017)
db = client.dbrecipe

from datetime import datetime

@app.route('/')
def home():
    return render_template('index.html')

# 전체 레시피 리스트
@app.route('/recipe', methods=['GET'])
def recipe_list():
    recipe_list = list(db.recipe_basic.find({},{'_id':False}))[:5] # 테스트용 상위 5개 데이터
    return jsonify({'recipe_list':recipe_list})

# 레시피 상세정보 API
@app.route('/recipe/detail', methods=['GET'])
def get_recipe_detail():
    recipe_id = int(request.args.get("recipe_id"))

    # 레시피 정보
    projection = {"RECIPE_ID": True, "RECIPE_NM_KO": True, "SUMRY": True, "NATION_NM": True,
                  "COOKING_TIME": True, "QNT": True, "IMG_URL": True, "Liked":True, "_id": False}
    info = db.recipe_basic.find_one({"RECIPE_ID": recipe_id}, projection)

    # 상세정보(조리과정)
    projection = {"COOKING_NO": True, "COOKING_DC": True, "_id": False}
    detail = list(db.recipe_number.find({"RECIPE_ID": recipe_id}, projection).sort("Liked",-1))

    return jsonify({"info":info, "detail": detail})

# 댓글 목록 API
@app.route('/recipe/comment', methods=['GET'])
def get_comments():
    recipe_id = int(request.args.get("recipe_id"))
    print(recipe_id)
    comments = list(db.comment.find({"RECIPE_ID": recipe_id}, {"_id": False}))
    print(f'comments = {comments}')

    return jsonify(comments)


# 댓글 작성 API
@app.route('/recipe/comment', methods=['POST'])
def save_comment():
    recipe_id = int(request.form["recipe_id"])
    text = request.form["text"]

    # [업로드 이미지 처리]
    # 클라이언트가 업로드한 파일을 서버에 저장
    fname = ""
    extension = ""
    today = today = datetime.now()  # 현재 시각 가져오기
    if len(request.files) != 0:
        file = request.files["img_src"]

        # 이미지 확장자
        # 가장 마지막 문자열 가져오기 [-1]
        ### 아이폰 heic 확장자 이미지 예외처리 필요
        extension = file.filename.split('.')[-1]

        today = datetime.now()  # 현재 시각 가져오기
        time = today.strftime('%Y-%m-%d-%H-%M-%S')
        fname = f'file-{time}.{extension}'

        save_to = f'static/images/{fname}'  # python f-string
        file.save(save_to)  # 날짜 기반 새로운 파일 이름 생성 후 프로젝트 static/images/ 폴더에 저장

        print(recipe_id, text, file)

    # 업데이트 날짜 표시
    date = today.strftime('%Y.%m.%d')

    # [DB 처리]
    doc = {
        'RECIPE_ID': recipe_id,
        'TEXT': text,
        'IMG_SRC': fname,
        'DATE': date
    }

    db.comment.insert_one(doc)

    return jsonify({'result': 'success'})

# 좋아요 누르기
@app.route('/recipe/like', methods=['PUT'])
def set_like():
    recipe_id = request.form['recipe_id']
    target_recipe = list(db.recipe_basic.find({"RECIPE_ID": int(recipe_id)}))
    current_like = target_recipe[0]["Liked"]
    new_like = current_like + 1
    db.recipe_basic.update_one({"RECIPE_ID": int(recipe_id)}, {'$set': {"Liked": int(new_like)}})
    return jsonify({"msg":"좋아요가 추가되었습니다."}) 

# 좋아요 해제
@app.route('/recipe/unlike', methods=['PUT'])
def set_unlike():
    recipe_id = request.form['recipe_id']
    target_recipe = list(db.recipe_basic.find({"RECIPE_ID": int(recipe_id)}))
    current_like = target_recipe[0]["Liked"]
    new_like = current_like - 1
    db.recipe_basic.update_one({"RECIPE_ID": int(recipe_id)}, {'$set': {"Liked": int(new_like)}})
    return jsonify({"msg":"좋아요가 해제되었습니다."}) 

# 좋아요 탭
@app.route('/recipe/liked', methods=['GET'])
def get_recipe_liked():
    projection = {"RECIPE_ID": True, "RECIPE_NM_KO": True, "SUMRY": True, "NATION_NM": True,
            "COOKING_TIME": True, "QNT": True, "IMG_URL": True, "Liked":True, "_id": False}
    recipe_liked_list = list(db.recipe_basic.find({"Liked": {"$gte":1}}, projection).sort("Liked",-1))
    return jsonify({'recipe_liked':recipe_liked_list})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)