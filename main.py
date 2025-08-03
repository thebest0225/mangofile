from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS
import json
import uuid
import os
from datetime import datetime
import shutil
import re

app = Flask(__name__)
CORS(app)

# 차단할 User-Agent 패턴들
BLOCKED_USER_AGENTS = [
    r'.*bot.*', r'.*spider.*', r'.*crawler.*', r'.*scraper.*',
    r'Googlebot', r'Bingbot', r'Slurp', r'DuckDuckBot', r'Baiduspider',
    r'YandexBot', r'facebookexternalhit', r'Twitterbot', r'LinkedInBot',
    r'WhatsApp', r'Applebot', r'ia_archiver', r'curl', r'wget'
]

def is_blocked_user_agent(user_agent):
    """User-Agent가 차단 대상인지 확인"""
    if not user_agent:
        return False

    user_agent_lower = user_agent.lower()
    for pattern in BLOCKED_USER_AGENTS:
        if re.search(pattern.lower(), user_agent_lower):
            return True
    return False

@app.before_request
def block_bots():
    """모든 요청 전에 봇 차단 검사"""
    user_agent = request.headers.get('User-Agent', '')
    if is_blocked_user_agent(user_agent):
        abort(403)  # Forbidden

# 파일 업로드 설정
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# 로컬 저장소 디렉터리 설정
UPLOAD_DIR = 'uploads'
DATA_DIR = 'data'

# 디렉터리 생성
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

PASSWORD = '0225'

def get_posts_file():
    return os.path.join(DATA_DIR, 'posts.json')

def load_posts():
    posts_file = get_posts_file()
    if os.path.exists(posts_file):
        with open(posts_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_posts(posts):
    posts_file = get_posts_file()
    with open(posts_file, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/favicon2.png')
def favicon():
    return send_file('favicon2.png')

@app.route('/logo.png')
def logo():
    return send_file('logo.png')

@app.route('/robots.txt')
def robots():
    return send_file('robots.txt')

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
        page = int(request.args.get('page', 1))
        tag = request.args.get('tag', '')
        posts_per_page = 20
        
        all_posts = load_posts()
        
        # 태그 필터링
        if tag:
            if tag == '태그없음':
                filtered_posts = [post for post in all_posts if not post.get('tags') or len(post.get('tags', [])) == 0]
            else:
                filtered_posts = [post for post in all_posts if post.get('tags') and tag in post.get('tags', [])]
        else:
            filtered_posts = all_posts
        
        # 페이지네이션
        start_idx = (page - 1) * posts_per_page
        end_idx = start_idx + posts_per_page
        posts = filtered_posts[start_idx:end_idx]
        
        total_pages = (len(filtered_posts) + posts_per_page - 1) // posts_per_page
        
        # 모든 태그 수집
        all_tags = set()
        has_no_tag_posts = False
        
        for post in all_posts:
            post_tags = post.get('tags', [])
            if post_tags:
                all_tags.update(post_tags)
            else:
                has_no_tag_posts = True
        
        all_tags = sorted(list(all_tags))
        if has_no_tag_posts:
            all_tags.append('태그없음')
        
        return jsonify({
            'posts': posts,
            'total_pages': total_pages,
            'current_page': page,
            'all_tags': all_tags
        })
    except Exception as e:
        print(f"Error loading posts: {str(e)}")
        return jsonify({
            'posts': [],
            'total_pages': 1,
            'current_page': 1,
            'all_tags': []
        })

@app.route('/posts', methods=['POST'])
def create_post():
    try:
        title = request.form.get('title')
        description = request.form.get('description')
        tags = request.form.get('tags', '')
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else []

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
                    # 안전한 파일명 생성
                    safe_filename = f"{post_id}_file_{i}_{file.filename}"
                    file_path = os.path.join(UPLOAD_DIR, safe_filename)

                    # 파일 크기 확인 (100MB 제한)
                    file.seek(0, os.SEEK_END)
                    file_size = file.tell()
                    file.seek(0)

                    if file_size > 200 * 1024 * 1024:  # 200MB
                        return jsonify({'error': f'{file.filename} 파일이 200MB를 초과합니다.'}), 400

                    # 로컬 파일 시스템에 저장
                    file.save(file_path)

                    files.append({
                        'id': safe_filename,
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
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'tags': tag_list
        }

        # 기존 게시글 목록 가져오기
        posts = load_posts()
        posts.insert(0, post)

        # 게시글 목록 저장
        save_posts(posts)

        return jsonify({'success': True, 'post': post})

    except Exception as e:
        print(f"Upload error: {str(e)}")
        return jsonify({'error': f'업로드 실패: {str(e)}'}), 500

@app.route('/posts/<post_id>', methods=['PUT'])
def update_post(post_id):
    try:
        posts = load_posts()

        post_index = next((i for i, p in enumerate(posts) if p['id'] == post_id), None)
        if post_index is None:
            return jsonify({'error': '게시글을 찾을 수 없습니다.'}), 404

        title = request.form.get('title')
        description = request.form.get('description')
        tags = request.form.get('tags', '')
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else []

        # 기존 파일들 삭제 (새 파일이 업로드된 경우)
        old_files = posts[post_index]['files']
        if any(f'file_{i}' in request.files for i in range(4)):
            for file_info in old_files:
                old_file_path = os.path.join(UPLOAD_DIR, file_info['id'])
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)

        files = []

        # 새 파일 업로드 처리
        for i in range(4):
            file_key = f'file_{i}'
            desc_key = f'description_{i}'

            if file_key in request.files:
                file = request.files[file_key]
                if file.filename:
                    safe_filename = f"{post_id}_file_{i}_{file.filename}"
                    file_path = os.path.join(UPLOAD_DIR, safe_filename)

                    file.save(file_path)

                    files.append({
                        'id': safe_filename,
                        'name': file.filename,
                        'size': os.path.getsize(file_path),
                        'description': request.form.get(desc_key, '')
                    })

        # 파일이 새로 업로드되지 않은 경우 기존 파일 유지
        if not files:
            files = old_files

        posts[post_index].update({
            'title': title,
            'description': description,
            'files': files,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'tags': tag_list
        })

        save_posts(posts)

        return jsonify({'success': True, 'post': posts[post_index]})

    except Exception as e:
        print(f"Update error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/posts/<post_id>', methods=['DELETE'])
def delete_post(post_id):
    try:
        posts = load_posts()

        post_index = next((i for i, p in enumerate(posts) if p['id'] == post_id), None)
        if post_index is None:
            return jsonify({'error': '게시글을 찾을 수 없습니다.'}), 404

        # 파일들 삭제
        for file_info in posts[post_index]['files']:
            file_path = os.path.join(UPLOAD_DIR, file_info['id'])
            if os.path.exists(file_path):
                os.remove(file_path)

        # 게시글 삭제
        posts.pop(post_index)
        save_posts(posts)

        return jsonify({'success': True})

    except Exception as e:
        print(f"Delete error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<file_id>')
def download_file(file_id):
    try:
        file_path = os.path.join(UPLOAD_DIR, file_id)
        if not os.path.exists(file_path):
            return jsonify({'error': '파일을 찾을 수 없습니다.'}), 404

        # 원본 파일명 추출
        filename = file_id.split('_', 3)[-1] if '_' in file_id else file_id

        return send_file(file_path, as_attachment=True, download_name=filename)

    except Exception as e:
        print(f"Download error: {str(e)}")
        return jsonify({'error': '파일을 찾을 수 없습니다.'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)