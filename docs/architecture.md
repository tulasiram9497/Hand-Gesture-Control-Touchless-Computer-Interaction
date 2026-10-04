# Architecture

## Data flow

1. The camera captures frames from the local webcam.
2. A frame is passed into the hand tracker.
3. MediaPipe identifies the user's hand and extracts normalized landmarks.
4. The gesture recognizer evaluates the landmark geometry and classifies the current gesture.
5. The activation manager ensures open palm hold duration before enabling commands.
6. The dispatcher routes recognized gestures to mouse, volume, or presentation handlers.

## Components

### Camera layer

The camera layer is responsible for opening the local camera, reading frames, and exposing the latest image data. It isolates hardware dependencies so the project can be tested without a live webcam.

### Vision layer

The vision layer includes the hand tracker and gesture recognizer. It is responsible for:

- selecting the correct hand
- rejecting multiple-hand states
- converting landmarks into normalized coordinates
- evaluating geometric relationships
- returning a consistent gesture result object

### Safety layer

The activation manager prevents accidental commands by requiring an intentional open palm hold before the system becomes active. If the activation gesture disappears, the system resets to the inactive state.

### Control layer

The control layer handles:

- mouse movement and click actions
- system volume updates
- slide navigation actions

These controller classes are separated to keep OS automation local to a specific module and easier to swap across platforms.

## Browser demo architecture

The browser demo keeps everything client-side:

- camera permission is requested explicitly
- MediaPipe runs in the browser
- landmark rendering happens in canvas
- no webcam frames are uploaded to a server

## Desktop architecture

The desktop app uses the same conceptual flow, but the final action layer interacts with host OS automation rather than simulated UI updates. This makes the repository adaptable for Python-based local control while retaining the same recognition logic.

## Browser limitations

A webpage cannot directly interface with the operating system’s mouse, keyboard, or global audio in the same way as a native desktop app. That is why the browser demo simulates the actions locally.
