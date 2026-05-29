
import numpy as np
import cv2
import math

def create_basic_video():
    width, height = 1920, 1080
    fps = 30
    duration = 240  # 4 minutes
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('propertyyards_basic_demo.mp4', fourcc, fps, (width, height))
    
    # Create frames
    total_frames = fps * duration
    
    for frame_num in range(total_frames):
        # Calculate time in seconds
        t = frame_num / fps
        
        # Create frame
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Add animated background
        for y in range(height):
            for x in range(width):
                # Create gradient
                r = int(26 + 20 * math.sin(t * 0.5 + x * 0.001))
                g = int(26 + 20 * math.cos(t * 0.5 + y * 0.001))
                b = int(51 + 30 * math.sin(t * 0.3))
                frame[y, x] = [b, g, r]
        
        # Add content based on time
        if t < 5:
            # Logo
            cv2.putText(frame, "PropertyYards", (width//2 - 200, height//2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 5)
            cv2.putText(frame, "India's Premier Real Estate Platform", (width//2 - 350, height//2 + 80), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3)
        
        elif t < 15:
            # Statistics
            cv2.putText(frame, "Platform Statistics", (width//2 - 150, 200), 
                       cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
            
            stats = ["10,000+ Properties Listed", "50,000+ Happy Users", "500 Cr+ Transactions", "4.9 Star Rating"]
            for i, stat in enumerate(stats):
                cv2.putText(frame, stat, (width//2 - 150, 350 + i * 80), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 136), 3)
        
        elif t < 30:
            # Features
            cv2.putText(frame, "Revolutionary Features", (width//2 - 200, 250), 
                       cv2.FONT_HERSHEY_SIMPLEX, 2.2, (255, 255, 255), 3)
            
            features = ["Property Layout Designer", "Vastu Shastra Validation", "Astrology Insights", "Smart Messaging"]
            for i, feature in enumerate(features):
                cv2.putText(frame, f"{i+1}. {feature}", (width//2 - 250, 350 + i * 70), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 212, 255), 3)
        
        elif t < 60:
            # Demo sections
            sections = [
                ("AI-Powered Search", 30, 45),
                ("Layout Designer", 45, 60)
            ]
            
            for section, start, end in sections:
                if start <= t < end:
                    cv2.putText(frame, f"Demo: {section}", (width//2 - 150, height//2), 
                               cv2.FONT_HERSHEY_SIMPLEX, 2.5, (0, 212, 255), 3)
        
        elif t < 120:
            # Extended demo
            demos = [
                ("Vastu Analysis", 60, 75),
                ("Astrology Chat", 75, 90),
                ("Messaging System", 90, 105),
                ("Image Upload", 105, 120)
            ]
            
            for demo, start, end in demos:
                if start <= t < end:
                    cv2.putText(frame, f"Feature: {demo}", (width//2 - 150, height//2), 
                               cv2.FONT_HERSHEY_SIMPLEX, 2.5, (0, 255, 255), 3)
        
        elif t < 240:
            # Call to action
            cv2.putText(frame, "Download PropertyYards Today!", (width//2 - 350, height//2 - 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 2.5, (0, 255, 136), 3)
            cv2.putText(frame, "Available on iOS, Android & Web", (width//2 - 300, height//2 + 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
            cv2.putText(frame, "www.propertyyards.com", (width//2 - 200, height//2 + 120), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.8, (0, 212, 255), 3)
        
        # Add timestamp
        time_str = f"{int(t//60):02d}:{int(t%60):02d}"
        cv2.putText(frame, time_str, (50, height - 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Add logo
        cv2.putText(frame, "PropertyYards", (50, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
        
        out.write(frame)
    
    out.release()
    print("Basic video created successfully!")

if __name__ == "__main__":
    create_basic_video()
