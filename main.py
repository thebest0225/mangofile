from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from replit.object_storage import Client
import json
import uuid
import os
from datetime import datetime
import tempfile

app = Flask(__name__)
CORS(app)

# 파일 업로드 설정
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2GB
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Object Storage 클라이언트 초기화
storage = Client()

PASSWORD = '0225'

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/favicon2.png')
def favicon():
    return send_file('favicon2.png')

@app.route('/logo.png')
def logo():
    return send_file('logo.png')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    password = data.get('password')
    if password == PASSWORD:
        return jsonify({'success': True})
    return jsonify({'success': False}), 401

@app.route('/posts', methods=['GET'])
def get_posts():
    try:
        posts_data = storage.download_from_text('posts.json')
        posts = json.loads(posts_data)
        return jsonify(posts)
    except:
        return jsonify([])

@app.route('/posts', methods=['POST'])
def create_post():
    try:
        title = request.form.get('title')
        description = request.form.get('description')

        if not title:
            return jsonify({'error': '제목을 입력해주세요.'}), 400

        post_id = str(uuid.uuid4())
        files = []

        # 파일 업로드 처리
        for i in range(4):
            file_key = f'file_{i}'
            desc_key = f'description_{i}'

            if file_key in request.files:
                file = request.files[file_key]
                if file.filename:
                    file_id = f"{post_id}_file_{i}_{file.filename}"

                    # 파일 크기 확인 (2GB 제한)
                    file.seek(0, os.SEEK_END)
                    file_size = file.tell()
                    file.seek(0)

                    if file_size > 2 * 1024 * 1024 * 1024:  # 2GB
                        return jsonify({'error': f'{file.filename} 파일이 2GB를 초과합니다.'}), 400

                    # Object Storage에 파일 저장
                    file_data = file.read()
                    file.seek(0)  # 파일 포인터 리셋
                    storage.upload_from_bytes(file_id, file_data)

                    files.append({
                        'id': file_id,
                        'name': file.filename,
                        'size': file_size,
                        'description': request.form.get(desc_key, '')
                    })

        # 게시글 데이터 생성
        post = {
            'id': post_id,
            'title': title,
            'description': description,
            'files': files,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # 기존 게시글 목록 가져오기
        try:
            posts_data = storage.download_from_text('posts.json')
            posts = json.loads(posts_data)
        except:
            posts = []

        posts.insert(0, post)

        # 게시글 목록 저장
        storage.upload_from_text('posts.json', json.dumps(posts, ensure_ascii=False))

        return jsonify({'success': True, 'post': post})

    except Exception as e:
        print(f"Upload error: {str(e)}")  # 서버 로그에 에러 출력
        return jsonify({'error': f'업로드 실패: {str(e)}'}), 500

@app.route('/posts/<post_id>', methods=['PUT'])
def update_post(post_id):
    try:
        # 기존 게시글 찾기
        posts_data = storage.download_from_text('posts.json')
        posts = json.loads(posts_data)

        post_index = next((i for i, p in enumerate(posts) if p['id'] == post_id), None)
        if post_index is None:
            return jsonify({'error': '게시글을 찾을 수 없습니다.'}), 404

        title = request.form.get('title')
        description = request.form.get('description')

        # 기존 파일들 삭제 (새 파일이 업로드된 경우)
        old_files = posts[post_index]['files']
        if any(f'file_{i}' in request.files for i in range(4)):
            for file_info in old_files:
                try:
                    storage.delete(file_info['id'])
                except:
                    pass

        files = []

        # 새 파일 업로드 처리
        for i in range(4):
            file_key = f'file_{i}'
            desc_key = f'description_{i}'

            if file_key in request.files:
                file = request.files[file_key]
                if file.filename:
                    file_id = f"{post_id}_file_{i}_{file.filename}"
                    # Object Storage에 파일 저장
                    file_data = file.read()
                    file.seek(0)  # 파일 포인터 리셋
                    storage.upload_from_bytes(file_id, file_data)

                    files.append({
                        'id': file_id,
                        'name': file.filename,
                        'size': len(file.read()),
                        'description': request.form.get(desc_key, '')
                    })
                    file.seek(0)

        # 파일이 새로 업로드되지 않은 경우 기존 파일 유지
        if not files:
            files = old_files

        posts[post_index].update({
            'title': title,
            'description': description,
            'files': files,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

        storage.upload_from_text('posts.json', json.dumps(posts, ensure_ascii=False))

        return jsonify({'success': True, 'post': posts[post_index]})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/posts/<post_id>', methods=['DELETE'])
def delete_post(post_id):
    try:
        posts_data = storage.download_from_text('posts.json')
        posts = json.loads(posts_data)

        post_index = next((i for i, p in enumerate(posts) if p['id'] == post_id), None)
        if post_index is None:
            return jsonify({'error': '게시글을 찾을 수 없습니다.'}), 404

        # 파일들 삭제
        for file_info in posts[post_index]['files']:
            try:
                storage.delete(file_info['id'])
            except:
                pass

        # 게시글 삭제
        posts.pop(post_index)
        storage.upload_from_text('posts.json', json.dumps(posts, ensure_ascii=False))

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<file_id>')
def download_file(file_id):
    try:
        # 임시 파일로 다운로드
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            storage.download_file(file_id, tmp_file.name)

            # 원본 파일명 추출
            filename = file_id.split('_', 3)[-1] if '_' in file_id else file_id

            return send_file(tmp_file.name, as_attachment=True, download_name=filename)

    except Exception as e:
        return jsonify({'error': '파일을 찾을 수 없습니다.'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)