import cv2
import sys

try:
    print("Opening Webcam...")
    print("Press 'Q' or 'ESC' to close\n")

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print(" Camera not detected at index 0 - Trying index 1...")
        cap = cv2.VideoCapture(1)

        if not cap.isOpened():
            print("Camera not found!")
            print("\nTroubleshooting:")
            print("   1. Check if webcam is connected")
            print("   2. Check Device Manager")
            print("   3. Try different index: 0, 1, 2")
            sys.exit(1)

    print("Camera opened successfully!")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    print(f"   Resolution: {width}x{height} @ {fps} FPS")
    print("\nDisplaying live webcam feed...\n")

    window_name = "Webcam Feed (Press Q or ESC to Exit)"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    cv2.resizeWindow(window_name, 1920, 1080)

    frame_count = 0

    while True:
        ret, frame = cap.read()

        if not ret:
            print("Failed to grab frame")
            break

        frame_count += 1

        display_frame = cv2.resize(frame, (1920, 1080))

        cv2.putText(display_frame, f"Frame: {frame_count}", (20, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 2)
        cv2.putText(display_frame, f"Resolution: {width}x{height}", (20, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow(window_name, display_frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('q') or key == 27:
            print(f"\nWebcam closed")
            print(f"   Total frames captured: {frame_count}")
            break

    cap.release()
    cv2.destroyAllWindows()

except KeyboardInterrupt:
    print("\n\n⚠ Stopped by user")
    cap.release()
    cv2.destroyAllWindows()
except Exception as e:
    print(f" Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
