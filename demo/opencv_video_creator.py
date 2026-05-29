#!/usr/bin/env python3
"""
PropertyYards Demo Video Creator using OpenCV
Creates an actual MP4 video file with visual content
"""

import numpy as np
import cv2
import math
import time
from pathlib import Path

def create_propertyyards_video():
    """Create PropertyYards demo video using OpenCV"""
    
    print("Creating PropertyYards Demo Video with OpenCV...")
    
    demo_dir = Path("demo")
    demo_dir.mkdir(exist_ok=True)
    
    # Video specifications
    width, height = 1920, 1080
    fps = 30
    duration = 240  # 4 minutes
    total_frames = fps * duration
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    output_path = demo_dir / 'propertyyards_demo_opencv.mp4'
    
    try:
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
        
        print(f"Generating {total_frames} frames...")
        
        for frame_num in range(total_frames):
            # Calculate time in seconds
            t = frame_num / fps
            
            # Create frame
            frame = create_frame(frame_num, t, width, height)
            
            out.write(frame)
            
            # Progress indicator
            if frame_num % 1000 == 0:
                progress = (frame_num / total_frames) * 100
                print(f"Progress: {progress:.1f}%")
        
        out.release()
        print(f"Video created successfully: {output_path}")
        print(f"Duration: {duration} seconds")
        print(f"Resolution: {width}x{height}")
        print(f"File size: {output_path.stat().st_size / (1024*1024):.1f} MB")
        
        return True
        
    except Exception as e:
        print(f"Error creating video: {e}")
        return False

def create_frame(frame_num, t, width, height):
    """Create a single video frame"""
    
    # Create gradient background
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Animated gradient background
    for y in range(height):
        for x in range(width):
            # Create animated gradient
            r = int(26 + 20 * math.sin(t * 0.5 + x * 0.001))
            g = int(26 + 20 * math.cos(t * 0.5 + y * 0.001))
            b = int(51 + 30 * math.sin(t * 0.3))
            frame[y, x] = [b, g, r]
    
    # Add content based on time
    if t < 5:
        # Opening scene - Logo
        add_text(frame, "PropertyYards", width//2, height//2 - 50, 3, (255, 255, 255), True)
        add_text(frame, "India's Premier Real Estate Platform", width//2, height//2 + 50, 1.5, (0, 255, 255), True)
        add_text(frame, "Where Technology Meets Tradition", width//2, height//2 + 120, 1.2, (0, 255, 0), True)
        
    elif t < 15:
        # Statistics
        add_text(frame, "Platform Statistics", width//2, 200, 2, (255, 255, 255), True)
        
        stats = [
            "10,000+ Properties Listed",
            "50,000+ Happy Users",
            "500 Cr+ Transactions",
            "4.9 Star User Rating"
        ]
        
        for i, stat in enumerate(stats):
            y_pos = 350 + i * 80
            add_text(frame, stat, width//2, y_pos, 1.5, (0, 255, 136), True)
            
    elif t < 20:
        # Features overview
        add_text(frame, "Revolutionary Features", width//2, 300, 2.2, (255, 255, 255), True)
        add_text(frame, "Experience the future of real estate", width//2, 400, 1.3, (0, 212, 255), True)
        
    elif t < 30:
        # Core features list
        add_text(frame, "Core Features", width//2, 250, 2, (255, 255, 255), True)
        
        features = [
            "1. Property Layout Designer",
            "2. Vastu Shastra Validation",
            "3. Astrology Insights",
            "4. Smart Messaging System"
        ]
        
        for i, feature in enumerate(features):
            y_pos = 350 + i * 70
            add_text(frame, feature, width//2, y_pos, 1.3, (0, 212, 255), True)
            
    elif t < 45:
        # AI-Powered Search
        add_text(frame, "AI-Powered Property Search", width//2, 250, 2, (255, 255, 255), True)
        
        search_features = [
            "Intelligent Recommendations",
            "Advanced Filtering Options",
            "Real-time Property Updates",
            "Personalized Search Results"
        ]
        
        for i, feature in enumerate(search_features):
            y_pos = 350 + i * 70
            add_text(frame, feature, width//2, y_pos, 1.3, (0, 255, 136), True)
            
    elif t < 60:
        # Vastu Shastra
        add_text(frame, "Vastu Shastra Integration", width//2, 250, 2, (255, 255, 255), True)
        
        vastu_features = [
            "8-Direction Analysis",
            "Energy Flow Optimization",
            "Personalized Remedies",
            "Traditional Wisdom + Modern Tech"
        ]
        
        for i, feature in enumerate(vastu_features):
            y_pos = 350 + i * 70
            add_text(frame, feature, width//2, y_pos, 1.3, (255, 107, 107), True)
            
    elif t < 75:
        # Astrology Insights
        add_text(frame, "Astrology & Birth Charts", width//2, 250, 2, (255, 255, 255), True)
        
        astrology_features = [
            "Personalized Predictions",
            "Career Guidance",
            "Relationship Insights",
            "AI Astrologer Chat"
        ]
        
        for i, feature in enumerate(astrology_features):
            y_pos = 350 + i * 70
            add_text(frame, feature, width//2, y_pos, 1.3, (233, 30, 99), True)
            
    elif t < 90:
        # Chat System
        add_text(frame, "Advanced Chat System", width//2, 250, 2, (255, 255, 255), True)
        
        chat_features = [
            "Real-time Messaging",
            "Team Collaboration",
            "Client Communication",
            "File Sharing & Media"
        ]
        
        for i, feature in enumerate(chat_features):
            y_pos = 350 + i * 70
            add_text(frame, feature, width//2, y_pos, 1.3, (76, 175, 80), True)
            
    elif t < 210:
        # Platform demo sequence
        demo_scenes = [
            ("Property Search", 210, 240),
            ("Layout Designer", 240, 270),
            ("Vastu Analysis", 270, 300),
            ("Astrology Chat", 300, 330),
            ("Messaging System", 330, 360),
            ("Image Upload", 360, 390),
            ("Rewards System", 390, 420),
            ("Analytics Dashboard", 420, 450),
            ("Multilingual Support", 450, 480),
            ("Mobile App", 480, 510),
            ("User Dashboard", 510, 540),
            ("Admin Panel", 540, 570),
            ("Property Listings", 570, 600),
            ("Client Management", 600, 630),
            ("Vendor Coordination", 630, 660),
            ("Team Collaboration", 660, 690),
            ("Reports & Analytics", 690, 720),
            ("Settings & Preferences", 720, 750),
            ("Help & Support", 750, 780),
            ("Notifications", 780, 810),
            ("Profile Management", 810, 840)
        ]
        
        current_time = t * 10  # Convert to frame time
        for scene_name, start, end in demo_scenes:
            if start <= current_time < end:
                add_text(frame, f"Demo: {scene_name}", width//2, height//2, 2.5, (0, 212, 255), True)
                
                # Add animated elements
                for i in range(5):
                    x = width//2 + int(200 * math.sin(current_time * 0.1 + i))
                    y = height//2 + 100 + i * 30
                    cv2.circle(frame, (x, y), 10, (0, 255, 255), -1)
                break
                
    elif t < 240:
        # Call to action
        add_text(frame, "Download PropertyYards Today!", width//2, 350, 2.5, (0, 255, 136), True)
        add_text(frame, "Available on iOS, Android & Web", width//2, 450, 1.5, (255, 255, 255), True)
        add_text(frame, "www.propertyyards.com", width//2, 550, 1.8, (0, 212, 255), True)
        
    # Add timestamp
    time_str = f"{int(t//60):02d}:{int(t%60):02d}"
    add_text(frame, time_str, 100, height - 50, 1, (255, 255, 255), False)
    
    # Add PropertyYards logo
    add_text(frame, "🏘️ PropertyYards", 100, 50, 1.5, (255, 255, 255), False)
    
    return frame

def add_text(frame, text, x, y, scale, color, center):
    """Add text to frame"""
    font = cv2.FONT_HERSHEY_SIMPLEX
    thickness = 2
    
    if center:
        # Get text size to center it
        (text_width, text_height), baseline = cv2.getTextSize(text, font, scale, thickness)
        x -= text_width // 2
        y += text_height // 2
    
    cv2.putText(frame, text, (x, y), font, scale, color, thickness, cv2.LINE_AA)

def create_audio_file():
    """Create a simple audio file"""
    
    print("Creating simple audio track...")
    
    try:
        import wave
        import struct
        
        sample_rate = 44100
        duration = 240
        frequency = 440  # A4 note
        
        # Generate audio data
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio = np.sin(2 * np.pi * frequency * t) * 0.1
        
        # Add some variation
        for i in range(0, len(audio), sample_rate):
            freq_variation = np.sin(2 * np.pi * 0.5 * i / sample_rate)
            audio[i:i+sample_rate] *= (1 + 0.3 * freq_variation)
        
        # Convert to 16-bit integers
        audio_int = (audio * 32767).astype(np.int16)
        
        # Create WAV file
        demo_dir = Path("demo")
        demo_dir.mkdir(exist_ok=True)
        
        with wave.open(str(demo_dir / 'propertyyards_audio.wav'), 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_int.tobytes())
        
        print("Audio file created successfully!")
        return True
        
    except Exception as e:
        print(f"Error creating audio: {e}")
        return False

def main():
    """Main function"""
    
    print("PropertyYards Demo Video Creator")
    print("=" * 50)
    
    # Create video
    if create_propertyyards_video():
        print("\nVideo creation completed!")
        
        # Create audio
        create_audio_file()
        
        print("\nNext Steps:")
        print("1. Install FFmpeg to combine video and audio")
        print("2. Use professional video editing software")
        print("3. Add voice narration and background music")
        print("4. Include actual screen recordings")
        
        demo_dir = Path("demo")
        video_path = demo_dir / 'propertyyards_demo_opencv.mp4'
        
        if video_path.exists():
            size_mb = video_path.stat().st_size / (1024 * 1024)
            print(f"\nVideo Details:")
            print(f"File: {video_path}")
            print(f"Size: {size_mb:.1f} MB")
            print(f"Duration: 4 minutes")
            print(f"Resolution: 1920x1080")
            print(f"You can now play this video in any media player!")
        
    else:
        print("Video creation failed. Please check requirements.")

if __name__ == "__main__":
    main()
