let allStories = [];
let currentUserStoryIndex = -1;
let currentItemIndex = -1;
let storyTimer = null;
let currentProgressBar = null;

async function loadStories() {
    try {
        const response = await fetch('/api/stories');
        allStories = await response.json();
        renderStoryTray();
    } catch (e) {
        console.error("Error loading stories:", e);
    }
}

function renderStoryTray() {
    const tray = document.getElementById('story-tray');
    // keep the first item (Own Story Button)
    const ownBtn = tray.children[0];
    tray.innerHTML = '';
    tray.appendChild(ownBtn);

    allStories.forEach((userObj, userIndex) => {
        const hasUnviewed = userObj.items.some(item => !item.viewed_by_me);
        const borderColor = hasUnviewed ? 'var(--accent-orange)' : 'rgba(255,255,255,0.3)';
        
        const div = document.createElement('div');
        div.className = 'story-item';
        div.style = 'display: flex; flex-direction: column; align-items: center; cursor: pointer; min-width: 50px;';
        div.onclick = () => openStoryViewer(userIndex);
        
        div.innerHTML = `
            <img src="${userObj.avatar}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; border: 2px solid ${borderColor}; padding: 2px;">
            <span style="font-size: 10px; margin-top: 2px; color: white; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 50px;">${userObj.username}</span>
        `;
        tray.appendChild(div);
    });
}

function openAddStoryModal() {
    document.getElementById('addStoryModal').style.display = 'flex';
}

function openStoryViewer(userIndex) {
    if(userIndex < 0 || userIndex >= allStories.length) return;
    currentUserStoryIndex = userIndex;
    
    // Find first unviewed, or start from 0
    const userObj = allStories[currentUserStoryIndex];
    let firstUnviewed = userObj.items.findIndex(item => !item.viewed_by_me);
    if(firstUnviewed === -1) firstUnviewed = 0;
    
    currentItemIndex = firstUnviewed;
    
    document.getElementById('storyViewerModal').style.display = 'flex';
    document.body.style.overflow = 'hidden'; // block scrolling
    showCurrentStoryItem();
}

function closeStoryViewer() {
    document.getElementById('storyViewerModal').style.display = 'none';
    document.body.style.overflow = '';
    clearTimeout(storyTimer);
    const vid = document.getElementById('sv-vid');
    vid.pause();
    vid.src = "";
    loadStories(); // refresh tray
}

function showCurrentStoryItem() {
    clearTimeout(storyTimer);
    
    const userObj = allStories[currentUserStoryIndex];
    if(!userObj || currentItemIndex >= userObj.items.length) {
        // go to next user
        if(currentUserStoryIndex + 1 < allStories.length) {
            openStoryViewer(currentUserStoryIndex + 1);
        } else {
            closeStoryViewer();
        }
        return;
    }
    if(currentItemIndex < 0) {
        if(currentUserStoryIndex - 1 >= 0) {
            openStoryViewer(currentUserStoryIndex - 1);
        } else {
            closeStoryViewer();
        }
        return;
    }
    
    const item = userObj.items[currentItemIndex];
    
    // Header
    document.getElementById('sv-avatar').src = userObj.avatar;
    document.getElementById('sv-username').innerText = userObj.username;
    document.getElementById('sv-time').innerText = new Date(item.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    
    // Progress Bars
    const progCont = document.getElementById('story-progress-container');
    progCont.innerHTML = '';
    userObj.items.forEach((it, idx) => {
        const barWrap = document.createElement('div');
        barWrap.style = 'flex: 1; height: 3px; background: rgba(255,255,255,0.3); border-radius: 2px; overflow: hidden;';
        
        const barFill = document.createElement('div');
        barFill.id = `sv-prog-${idx}`;
        barFill.style.height = '100%';
        barFill.style.background = 'white';
        barFill.style.width = idx < currentItemIndex ? '100%' : '0%';
        barFill.style.transition = 'width linear';
        
        barWrap.appendChild(barFill);
        progCont.appendChild(barWrap);
    });
    
    currentProgressBar = document.getElementById(`sv-prog-${currentItemIndex}`);
    
    // Media
    const imgEl = document.getElementById('sv-img');
    const vidEl = document.getElementById('sv-vid');
    
    imgEl.style.display = 'none';
    vidEl.style.display = 'none';
    
    // Mark viewed
    if(!item.viewed_by_me) {
        fetch(`/api/story/${item.id}/view`, { method: 'POST' });
        item.viewed_by_me = true;
    }
    
    // Likes
    const likeBtn = document.getElementById('sv-like-btn');
    likeBtn.innerText = item.liked_by_me ? '❤️' : '🤍';
    document.getElementById('sv-like-count').innerText = item.likes.length > 0 ? item.likes.length : '';
    
    // Viewers list (only if it's my own story)
    const viewersCont = document.getElementById('sv-viewers-container');
    const myUsername = document.querySelector('.profile-avatar-small').nextElementSibling.innerText.trim();
    if(userObj.username === myUsername) {
        viewersCont.style.display = 'block';
        const vList = document.getElementById('sv-viewers-list');
        vList.innerHTML = '';
        item.viewers.forEach(v => {
            vList.innerHTML += `<div style="display:flex; flex-direction:column; align-items:center;"><img src="${v.avatar}" style="width:30px; height:30px; border-radius:50%;"><span style="color:white; font-size:10px;">${v.username}</span></div>`;
        });
        if(item.viewers.length === 0) vList.innerHTML = '<span style="color:#aaa; font-size:12px;">Henüz kimse görmedi.</span>';
    } else {
        viewersCont.style.display = 'none';
    }

    if(item.is_video) {
        vidEl.src = item.media;
        vidEl.style.display = 'block';
        vidEl.onloadedmetadata = () => {
            const duration = vidEl.duration * 1000;
            animateProgress(duration);
            storyTimer = setTimeout(nextStoryItem, duration);
        };
        vidEl.play();
    } else {
        imgEl.src = item.media;
        imgEl.style.display = 'block';
        const duration = 10000;
        animateProgress(duration);
        storyTimer = setTimeout(nextStoryItem, duration);
    }
}

function animateProgress(duration) {
    if(!currentProgressBar) return;
    // reset
    currentProgressBar.style.transition = 'none';
    currentProgressBar.style.width = '0%';
    
    // force reflow
    void currentProgressBar.offsetWidth;
    
    currentProgressBar.style.transition = `width ${duration}ms linear`;
    currentProgressBar.style.width = '100%';
}

function nextStoryItem() {
    if(currentProgressBar) currentProgressBar.style.width = '100%';
    currentItemIndex++;
    showCurrentStoryItem();
}

function prevStoryItem() {
    if(currentProgressBar) currentProgressBar.style.width = '0%';
    currentItemIndex--;
    showCurrentStoryItem();
}

async function likeCurrentStory() {
    const userObj = allStories[currentUserStoryIndex];
    const item = userObj.items[currentItemIndex];
    
    const response = await fetch(`/api/story/${item.id}/like`, { method: 'POST' });
    const data = await response.json();
    
    if(data.success) {
        if(data.action === 'liked') {
            item.liked_by_me = true;
            item.likes.push({}); // dummy for count
        } else {
            item.liked_by_me = false;
            item.likes.pop();
        }
        // update UI immediately
        const likeBtn = document.getElementById('sv-like-btn');
        likeBtn.innerText = item.liked_by_me ? '❤️' : '🤍';
        document.getElementById('sv-like-count').innerText = item.likes.length > 0 ? item.likes.length : '';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadStories();
});
