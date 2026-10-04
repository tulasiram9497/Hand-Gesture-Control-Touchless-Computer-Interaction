# Troubleshooting

## Camera permission denied

- Check browser permissions if using the web demo.
- Make sure no other app is already using the camera.
- Test the camera in another app to confirm the device is healthy.

## No hand detected

- Move the hand to the center of the frame.
- Ensure good lighting and avoid strong shadows.
- Keep fingers visible and separated.
- Use the system in a steady camera position.

## Multiple hands detected

- Keep one hand in frame.
- Avoid showing both hands at the same time.
- Reduce background motion and ensure the camera has a clear subject.

## Missing dependency

Install the project dependencies:

```bash
pip install -r requirements.txt
```

## Unsupported operating system behavior

The project isolates OS-specific logic behind controller interfaces. If by default a platform-specific integration is unavailable, the app logs a clear warning and continues with the local safety checks.

## Volume control not working

Check whether the system audio interface is available. Linux systems may need `amixer` or `pulseaudio` support.

## Presentation controls not working

Ensure the target application is active and the key mapping matches the presentation tool in use. The default mappings are:

- next: right arrow
- previous: left arrow

## Mouse movement feels unstable

- reduce the camera movement
- increase lighting consistency
- reduce sensitivity in the configuration file
- use the built-in smoothing configuration and dead-zone settings
