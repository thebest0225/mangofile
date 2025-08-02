
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
  document.getElementById('selectedFiles').innerHTML = '';
  document.getElementById('writeModal').style.display = 'block';
}

// 모달 닫기
function closeModal() {
  document.getElementById('writeModal').style.display = 'none';
}

function closeViewModal() {
  document.getElementById('viewModal').style.display = 'none';
}

// 파일 선택 이벤트 처리
document.getElementById('multipleFiles').addEventListener('change', function(e) {
  displaySelectedFiles(e.target.files);
});

function displaySelectedFiles(files) {
  const container = document.getElementById('selectedFiles');
  container.innerHTML = '';
  
  if (files.length > 4) {
    alert('최대 4개 파일까지만 업로드 가능합니다.');
    document.getElementById('multipleFiles').value = '';
    return;
  }
  
  Array.from(files).forEach((file, index) => {
    if (file.size > 500 * 1024 * 1024) {
      alert(`${file.name} 파일 크기가 500MB를 초과합니다.`);
      document.getElementById('multipleFiles').value = '';
      container.innerHTML = '';
      return;
    }
    
    const fileDiv = document.createElement('div');
    fileDiv.className = 'file-upload-group';
    fileDiv.innerHTML = `
      <div style="font-size: 11px; margin-bottom: 4px;">
        <strong>${file.name}</strong> (${formatFileSize(file.size)})
      </div>
      <input type="text" class="file-description form-control" placeholder="파일 설명" data-index="${index}">
    `;
    container.appendChild(fileDiv);
  });
}

// 글 저장
document.getElementById('postForm').addEventListener('submit', async function(e) {
  e.preventDefault();
  
  const title = document.getElementById('postTitle').value;
  const description = document.getElementById('postDescription').value;
  
  // 파일 정보 수집
  const files = [];
  const fileInput = document.getElementById('multipleFiles');
  const selectedFiles = fileInput.files;
  const fileDescriptions = document.querySelectorAll('.file-description');
  
  for (let i = 0; i < selectedFiles.length; i++) {
    const file = selectedFiles[i];
    const desc = fileDescriptions[i] ? fileDescriptions[i].value : '';
    
    // 파일을 Base64로 변환하여 저장
    const fileData = await fileToBase64(file);
    
    files.push({
      file: {
        name: file.name,
        size: file.size,
        type: file.type,
        data: fileData
      },
      description: desc
    });
  }
  
  // 빈 슬롯을 4개까지 채우기
  while (files.length < 4) {
    files.push({
      file: null,
      description: ''
    });
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
    uploadedFiles.forEach((f, idx) => {
      content += `
        <li style="margin-bottom: 8px;">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
              <strong>${f.file.name}</strong> (${formatFileSize(f.file.size)})
              ${f.description ? `<br><span style="color: #666; font-size: 11px;">${f.description}</span>` : ''}
            </div>
            <button onclick="downloadFile(${index}, ${idx})" class="btn btn-small" style="margin-left: 8px;">다운로드</button>
          </div>
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
  
  // 기존 파일 정보 표시 (파일은 다시 선택해야 함)
  const container = document.getElementById('selectedFiles');
  container.innerHTML = '';
  
  const uploadedFiles = post.files.filter(f => f.file);
  if (uploadedFiles.length > 0) {
    const infoDiv = document.createElement('div');
    infoDiv.style.cssText = 'background: #f0f0f0; padding: 8px; border-radius: 4px; margin-bottom: 8px; font-size: 11px;';
    infoDiv.innerHTML = `
      <strong>기존 파일:</strong><br>
      ${uploadedFiles.map(f => `• ${f.file.name} ${f.description ? `(${f.description})` : ''}`).join('<br>')}
      <br><br><em>파일을 수정하려면 다시 선택해주세요.</em>
    `;
    container.appendChild(infoDiv);
  }
  
  // 파일 입력 초기화
  document.getElementById('multipleFiles').value = '';
  
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

// 게시판 새로고침
function refreshBoard() {
  renderPosts();
}

// 파일을 Base64로 변환
function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result);
    reader.onerror = error => reject(error);
  });
}

// Base64를 Blob으로 변환
function base64ToBlob(base64, contentType) {
  const byteCharacters = atob(base64.split(',')[1]);
  const byteNumbers = new Array(byteCharacters.length);
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i);
  }
  const byteArray = new Uint8Array(byteNumbers);
  return new Blob([byteArray], { type: contentType });
}

// 파일 다운로드
function downloadFile(postIndex, fileIndex) {
  const post = posts[postIndex];
  const uploadedFiles = post.files.filter(f => f.file);
  const file = uploadedFiles[fileIndex];
  
  if (file && file.file && file.file.data) {
    try {
      const blob = base64ToBlob(file.file.data, file.file.type);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = file.file.name;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      alert('파일 다운로드 중 오류가 발생했습니다.');
      console.error('Download error:', error);
    }
  } else {
    alert('파일 데이터를 찾을 수 없습니다.');
  }
}

// 페이지 로드 시 로그인 확인
checkLogin();
