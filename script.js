
let posts = JSON.parse(localStorage.getItem('posts')) || [];
let currentEditId = null;
const PASSWORD = '0225';

// 로그인 확인
function checkLogin() {
  const isLoggedIn = sessionStorage.getItem('isLoggedIn');
  if (isLoggedIn === 'true') {
    showBoard();
  } else {
    showLogin();
  }
}

// 로그인 처리
function login() {
  const password = document.getElementById('password').value;
  if (password === PASSWORD) {
    sessionStorage.setItem('isLoggedIn', 'true');
    showBoard();
  } else {
    alert('비밀번호가 틀렸습니다.');
    document.getElementById('password').value = '';
  }
}

// 로그아웃
function logout() {
  sessionStorage.removeItem('isLoggedIn');
  showLogin();
}

// 로그인 화면 표시
function showLogin() {
  document.getElementById('loginForm').classList.remove('hidden');
  document.getElementById('boardContainer').classList.add('hidden');
}

// 게시판 화면 표시
function showBoard() {
  document.getElementById('loginForm').classList.add('hidden');
  document.getElementById('boardContainer').classList.remove('hidden');
  renderPosts();
}

// 게시글 목록 렌더링
function renderPosts() {
  const boardList = document.getElementById('boardList');
  
  if (posts.length === 0) {
    boardList.innerHTML = '<div style="padding: 20px; text-align: center; color: #666;">게시글이 없습니다.</div>';
    return;
  }

  boardList.innerHTML = posts.map((post, index) => `
    <div class="board-item" onclick="viewPost(${index})">
      <div class="post-title">${post.title}</div>
      <div class="post-meta">
        ${post.date} | 파일: ${post.files.filter(f => f.file).length}개
      </div>
    </div>
  `).join('');
}

// 글쓰기 모달 표시
function showWriteModal() {
  currentEditId = null;
  document.getElementById('modalTitle').textContent = '글쓰기';
  document.getElementById('postForm').reset();
  document.getElementById('writeModal').style.display = 'block';
}

// 모달 닫기
function closeModal() {
  document.getElementById('writeModal').style.display = 'none';
}

function closeViewModal() {
  document.getElementById('viewModal').style.display = 'none';
}

// 글 저장
document.getElementById('postForm').addEventListener('submit', function(e) {
  e.preventDefault();
  
  const title = document.getElementById('postTitle').value;
  const description = document.getElementById('postDescription').value;
  
  // 파일 정보 수집
  const files = [];
  const fileInputs = document.querySelectorAll('.file-input');
  const fileDescriptions = document.querySelectorAll('.file-description');
  
  for (let i = 0; i < 4; i++) {
    const file = fileInputs[i].files[0];
    const desc = fileDescriptions[i].value;
    
    if (file) {
      // 파일 크기 체크 (500MB)
      if (file.size > 500 * 1024 * 1024) {
        alert('파일 크기는 500MB를 초과할 수 없습니다.');
        return;
      }
      
      files.push({
        file: {
          name: file.name,
          size: file.size,
          type: file.type
        },
        description: desc
      });
    } else if (desc) {
      files.push({
        file: null,
        description: desc
      });
    } else {
      files.push({
        file: null,
        description: ''
      });
    }
  }
  
  const post = {
    title,
    description,
    files,
    date: new Date().toLocaleString('ko-KR')
  };
  
  if (currentEditId !== null) {
    posts[currentEditId] = post;
  } else {
    posts.unshift(post);
  }
  
  localStorage.setItem('posts', JSON.stringify(posts));
  renderPosts();
  closeModal();
});

// 글 보기
function viewPost(index) {
  const post = posts[index];
  currentEditId = index;
  
  document.getElementById('viewTitle').textContent = post.title;
  
  let content = `
    <div style="margin-bottom: 12px;">
      <strong>작성일:</strong> ${post.date}
    </div>
    <div style="margin-bottom: 12px;">
      <strong>설명:</strong><br>
      ${post.description || '설명 없음'}
    </div>
  `;
  
  const uploadedFiles = post.files.filter(f => f.file);
  if (uploadedFiles.length > 0) {
    content += '<div><strong>첨부파일:</strong><ul style="margin: 8px 0; padding-left: 20px;">';
    uploadedFiles.forEach(f => {
      content += `
        <li style="margin-bottom: 4px;">
          <strong>${f.file.name}</strong> (${formatFileSize(f.file.size)})
          ${f.description ? `<br><span style="color: #666; font-size: 11px;">${f.description}</span>` : ''}
        </li>
      `;
    });
    content += '</ul></div>';
  }
  
  document.getElementById('viewContent').innerHTML = content;
  document.getElementById('viewModal').style.display = 'block';
}

// 글 수정
function editPost() {
  const post = posts[currentEditId];
  
  document.getElementById('modalTitle').textContent = '글 수정';
  document.getElementById('postTitle').value = post.title;
  document.getElementById('postDescription').value = post.description;
  
  // 파일 설명 복원
  const fileDescriptions = document.querySelectorAll('.file-description');
  post.files.forEach((f, index) => {
    if (index < 4 && fileDescriptions[index]) {
      fileDescriptions[index].value = f.description || '';
    }
  });
  
  closeViewModal();
  document.getElementById('writeModal').style.display = 'block';
}

// 글 삭제
function deletePost() {
  if (confirm('정말 삭제하시겠습니까?')) {
    posts.splice(currentEditId, 1);
    localStorage.setItem('posts', JSON.stringify(posts));
    renderPosts();
    closeViewModal();
  }
}

// 파일 크기 포맷
function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 엔터키 로그인
document.getElementById('password').addEventListener('keypress', function(e) {
  if (e.key === 'Enter') {
    login();
  }
});

// 페이지 로드 시 로그인 확인
checkLogin();
