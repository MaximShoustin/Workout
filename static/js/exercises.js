// Video popup functionality
function openVideo(videoId) {
    document.getElementById(videoId).style.display = 'block';
}

function closeVideo(videoId) {
    document.getElementById(videoId).style.display = 'none';
    // Stop any playing videos
    const iframe = document.querySelector('#' + videoId + ' iframe');
    if (iframe) {
        iframe.src = iframe.src;
    }
    const video = document.querySelector('#' + videoId + ' video');
    if (video) {
        video.pause();
    }
}

// Close video when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('video-popup')) {
        event.target.style.display = 'none';
        // Stop any playing videos
        const iframe = event.target.querySelector('iframe');
        if (iframe) {
            iframe.src = iframe.src;
        }
        const video = event.target.querySelector('video');
        if (video) {
            video.pause();
        }
    }
}

