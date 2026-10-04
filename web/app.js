const video = document.getElementById('video');
const canvas = document.getElementById('landmarksCanvas');
const ctx = canvas.getContext('2d');
const startCameraBtn = document.getElementById('startCameraBtn');
const statusBadge = document.getElementById('statusBadge');
const gestureName = document.getElementById('gestureName');
const gestureConfidence = document.getElementById('gestureConfidence');
const volumeValue = document.getElementById('volumeValue');
const slideValue = document.getElementById('slideValue');
const activationText = document.getElementById('activationText');
const activationIndicator = document.getElementById('activationIndicator');
const cursor = document.getElementById('cursor');
const cameraReadout = document.getElementById('cameraReadout');
const trackingReadout = document.getElementById('trackingReadout');
const landmarkReadout = document.getElementById('landmarkReadout');

const state = {
  stream: null,
  running: false,
  processing: false,
  active: false,
  activationStartedAt: null,
  lastGesture: 'NONE',
  lastActionAt: 0,
  unknownSince: null,
  movementHistory: [],
  volume: 55,
  slide: 3,
  maxSlides: 10,
};

const hands = typeof Hands === 'undefined' ? null : new Hands({
  locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`,
});

if (hands) {
  hands.setOptions({
    maxNumHands: 1,
    modelComplexity: 1,
    minDetectionConfidence: 0.6,
    minTrackingConfidence: 0.6,
  });
  hands.onResults(onResults);
}

async function startCamera() {
  try {
    if (!hands) {
      throw new Error('Hand tracking library did not load. Check your internet connection and refresh.');
    }
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error('Your browser does not support webcam access.');
    }

    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user' },
      audio: false,
    });

    state.stream = stream;
    state.running = true;
    video.srcObject = stream;
    await video.play();
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    startCameraBtn.textContent = 'Stop Camera';
    statusBadge.textContent = 'READY';
    statusBadge.className = 'status-badge inactive';
    cameraReadout.textContent = `Camera: ${canvas.width} x ${canvas.height}`;
    trackingReadout.textContent = 'Hand: searching';
    updateVolumeUI();
    updateSlideUI();
    requestAnimationFrame(loopCam);
  } catch (error) {
    console.error(error);
    statusBadge.textContent = 'ERROR';
    statusBadge.className = 'status-badge inactive';
    activationText.textContent = error.message || 'Camera access denied';
    cameraReadout.textContent = `Camera error: ${error.message || 'permission denied'}`;
  }
}

function stopCamera() {
  state.running = false;
  state.active = false;
  state.activationStartedAt = null;
  state.lastGesture = 'NONE';
  state.movementHistory = [];
  if (state.stream) {
    state.stream.getTracks().forEach((track) => track.stop());
    state.stream = null;
  }
  startCameraBtn.textContent = 'Start Camera';
  statusBadge.textContent = 'INACTIVE';
  statusBadge.className = 'status-badge inactive';
  activationText.textContent = 'Camera stopped';
  activationIndicator.classList.remove('active');
  cursor.classList.remove('visible');
  cameraReadout.textContent = 'Camera: stopped';
  trackingReadout.textContent = 'Hand: not detected';
  landmarkReadout.textContent = 'Landmarks: --';
  gestureName.textContent = 'NONE';
  gestureConfidence.textContent = '0.00';
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (video.srcObject) {
    video.srcObject.getTracks().forEach((track) => track.stop());
    video.srcObject = null;
  }
}

function updateVolumeUI() {
  volumeValue.textContent = `${state.volume}%`;
}

function updateSlideUI() {
  slideValue.textContent = `${String(state.slide).padStart(2, '0')} / ${state.maxSlides}`;
}

function distance(a, b) {
  return Math.hypot(a.x - b.x, a.y - b.y);
}

function fingerExtended(landmarks, tipIndex, pipIndex) {
  return distance(landmarks[0], landmarks[tipIndex]) > distance(landmarks[0], landmarks[pipIndex]) * 1.08;
}

function classifyGesture(landmarks) {
  if (!landmarks || landmarks.length < 21) return { gesture: 'NONE', confidence: 0 };

  const wrist = landmarks[0];
  const middleMcp = landmarks[9];
  const palmCenter = { x: (wrist.x + middleMcp.x) / 2, y: (wrist.y + middleMcp.y) / 2 };
  state.movementHistory.push(palmCenter);
  if (state.movementHistory.length > 8) state.movementHistory.shift();
  if (state.movementHistory.length === 8) {
    const verticalDelta = palmCenter.y - state.movementHistory[0].y;
    if (Math.abs(verticalDelta) >= 0.035) {
      return {
        gesture: verticalDelta > 0 ? 'HAND_MOVING_DOWN' : 'HAND_MOVING_UP',
        confidence: Math.min(0.99, 0.65 + Math.abs(verticalDelta) * 4),
      };
    }
  }

  const thumbExtended = distance(landmarks[2], landmarks[4]) > distance(landmarks[2], landmarks[3]) * 1.12;
  const extended = {
    thumb: thumbExtended,
    index: fingerExtended(landmarks, 8, 6),
    middle: fingerExtended(landmarks, 12, 10),
    ring: fingerExtended(landmarks, 16, 14),
    pinky: fingerExtended(landmarks, 20, 18),
  };
  const palmScale = distance(wrist, middleMcp);
  const pinchRatio = palmScale > 0 ? distance(landmarks[4], landmarks[8]) / palmScale : 1;
  if (pinchRatio < 0.22) return { gesture: 'PINCH', confidence: 0.90 };

  const otherFingersCurled = !extended.index && !extended.middle && !extended.ring && !extended.pinky;
  const thumbDirection = landmarks[4].y - landmarks[3].y;
  if (thumbExtended && otherFingersCurled && thumbDirection < -0.015) {
    return { gesture: 'THUMBS_UP', confidence: 0.90 };
  }
  if (thumbExtended && otherFingersCurled && thumbDirection > 0.015) {
    return { gesture: 'THUMBS_DOWN', confidence: 0.90 };
  }

  const extendedCount = Object.values(extended).filter(Boolean).length;
  if (extendedCount >= 4) return { gesture: 'OPEN_PALM', confidence: 0.90 };
  if (extended.index && extended.middle && !extended.ring && !extended.pinky) {
    return { gesture: 'TWO_FINGERS', confidence: 0.88 };
  }
  if (extended.index && !extended.middle && !extended.ring && !extended.pinky) {
    return { gesture: 'ONE_FINGER', confidence: 0.85 };
  }
  return { gesture: 'NONE', confidence: 0 };
}

function updateActivation(gesture, handDetected) {
  if (!handDetected) {
    state.active = false;
    state.activationStartedAt = null;
    state.unknownSince = null;
    state.lastGesture = 'NONE';
    statusBadge.textContent = 'INACTIVE';
    statusBadge.className = 'status-badge inactive';
    activationText.textContent = 'Tracking lost';
    activationIndicator.classList.remove('active');
    return;
  }

  if (state.active) {
    if (gesture === 'NONE') {
      state.unknownSince ??= performance.now();
      if (performance.now() - state.unknownSince >= 2000) {
        state.active = false;
        statusBadge.textContent = 'INACTIVE';
        statusBadge.className = 'status-badge inactive';
        activationText.textContent = 'System inactive';
        activationIndicator.classList.remove('active');
      }
    } else {
      state.unknownSince = null;
      statusBadge.textContent = 'ACTIVE';
      statusBadge.className = 'status-badge active';
      activationText.textContent = 'System active';
      activationIndicator.classList.add('active');
    }
    return;
  }

  if (gesture === 'OPEN_PALM') {
    if (!state.activationStartedAt) {
      state.activationStartedAt = performance.now();
    }

    const holdTime = performance.now() - state.activationStartedAt;
    if (holdTime > 1500) {
      state.active = true;
      statusBadge.textContent = 'ACTIVE';
      statusBadge.className = 'status-badge active';
      activationText.textContent = 'System active';
      activationIndicator.classList.add('active');
      return;
    }

    activationText.textContent = `Activating... ${(holdTime / 1000).toFixed(1)}s`;
    activationIndicator.classList.remove('active');
    return;
  }

  state.activationStartedAt = null;
  activationIndicator.classList.remove('active');
  activationText.textContent = 'Waiting for open palm';
}

function onResults(results) {
  const canvasWidth = canvas.width;
  const canvasHeight = canvas.height;
  ctx.clearRect(0, 0, canvasWidth, canvasHeight);

  if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
    const landmarks = results.multiHandLandmarks[0];
    drawLandmarks(landmarks);

    const result = classifyGesture(landmarks);
    const gesture = result.gesture;
    gestureName.textContent = gesture;
    gestureConfidence.textContent = result.confidence.toFixed(2);
    trackingReadout.textContent = `Hand: tracked (${landmarks.length} points)`;
    landmarkReadout.textContent = `Wrist ${landmarks[0].x.toFixed(2)}, ${landmarks[0].y.toFixed(2)} | Index ${landmarks[8].x.toFixed(2)}, ${landmarks[8].y.toFixed(2)} | Thumb ${landmarks[4].x.toFixed(2)}, ${landmarks[4].y.toFixed(2)}`;

    updateActivation(gesture, true);

    if (state.active) {
      if (gesture === 'ONE_FINGER') {
        const x = landmarks[8].x * canvasWidth;
        const y = landmarks[8].y * canvasHeight;
        cursor.classList.add('visible');
        cursor.style.left = `${x}px`;
        cursor.style.top = `${y}px`;
      } else {
        cursor.classList.remove('visible');
      }
      dispatchGesture(gesture);
    }
  } else {
    state.movementHistory = [];
    gestureName.textContent = 'NONE';
    gestureConfidence.textContent = '0.00';
    trackingReadout.textContent = 'Hand: not detected';
    landmarkReadout.textContent = 'Landmarks: --';
    cursor.classList.remove('visible');
    updateActivation('NONE', false);
  }
}

function dispatchGesture(gesture) {
  if (gesture === 'NONE' || gesture.startsWith('HAND_MOVING_')) {
    state.lastGesture = gesture;
    return;
  }
  if (gesture === state.lastGesture) return;
  state.lastGesture = gesture;

  const now = performance.now();
  if (now - state.lastActionAt < 800) return;
  state.lastActionAt = now;

  if (gesture === 'THUMBS_UP') {
    state.volume = Math.min(100, state.volume + 4);
    updateVolumeUI();
  } else if (gesture === 'THUMBS_DOWN') {
    state.volume = Math.max(0, state.volume - 4);
    updateVolumeUI();
  } else if (gesture === 'TWO_FINGERS') {
    state.slide = Math.min(state.maxSlides, state.slide + 1);
    updateSlideUI();
  } else if (gesture === 'ONE_FINGER') {
    state.slide = Math.max(1, state.slide - 1);
    updateSlideUI();
  } else if (gesture === 'PINCH') {
    cursor.classList.add('visible');
  }
}

function drawLandmarks(landmarks) {
  const connections = [
    [0, 1], [1, 2], [2, 3], [3, 4],
    [0, 5], [5, 6], [6, 7], [7, 8],
    [5, 9], [9, 10], [10, 11], [11, 12],
    [9, 13], [13, 14], [14, 15], [15, 16],
    [13, 17], [17, 18], [18, 19], [19, 20],
    [0, 17], [5, 9], [9, 13]
  ];

  ctx.strokeStyle = 'rgba(184, 192, 255, 0.9)';
  ctx.lineWidth = 2;

  for (const [a, b] of connections) {
    const p1 = landmarks[a];
    const p2 = landmarks[b];
    ctx.beginPath();
    ctx.moveTo(p1.x * canvas.width, p1.y * canvas.height);
    ctx.lineTo(p2.x * canvas.width, p2.y * canvas.height);
    ctx.stroke();
  }

  for (const point of landmarks) {
    ctx.beginPath();
    ctx.arc(point.x * canvas.width, point.y * canvas.height, 4, 0, Math.PI * 2);
    ctx.fillStyle = '#f5f7fa';
    ctx.fill();
  }
}

async function loopCam() {
  if (!state.running) return;
  if (video.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA && !state.processing) {
    state.processing = true;
    try {
      await hands.send({ image: video });
    } catch (error) {
      console.error(error);
      cameraReadout.textContent = `Tracking error: ${error.message || 'frame processing failed'}`;
    } finally {
      state.processing = false;
    }
  }
  if (state.running) requestAnimationFrame(loopCam);
}

startCameraBtn.addEventListener('click', async () => {
  if (state.stream) {
    stopCamera();
    return;
  }
  await startCamera();
});

updateVolumeUI();
updateSlideUI();
