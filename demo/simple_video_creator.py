#!/usr/bin/env python3
"""
Simple PropertyYards Demo Video Creator
Creates an actual MP4 video file with basic content
"""

import os
import subprocess
import sys
from pathlib import Path

def create_video():
    """Create PropertyYards demo video"""
    
    print("Creating PropertyYards Demo Video...")
    
    demo_dir = Path("demo")
    demo_dir.mkdir(exist_ok=True)
    
    # Try to use FFmpeg to create a simple video
    try:
        # Create a simple color video with text overlays
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', 'color=c=001a33:size=1920x1080:duration=240:rate=30',
            '-vf',
            (
                "drawtext=text='PropertyYards - India\\'s Premier Real Estate Platform':"
                "fontsize=48:fontcolor=white:x=(w-text_w)/2:y=100:enable='between(t,0,5)',"
                "drawtext=text='10,000+ Properties Listed':fontsize=36:fontcolor=00ff88:"
                "x=200:y=300:enable='between(t,5,15)',"
                "drawtext=text='50,000+ Happy Users':fontsize=36:fontcolor=00ff88:"
                "x=200:y=350:enable='between(t,5,15)',"
                "drawtext=text='500 Cr+ Transactions':fontsize=36:fontcolor=00ff88:"
                "x=200:y=400:enable='between(t,5,15)',"
                "drawtext=text='4.9 Star User Rating':fontsize=36:fontcolor=00ff88:"
                "x=200:y=450:enable='between(t,5,15)',"
                "drawtext=text='Revolutionary Features':fontsize=42:fontcolor=white:"
                "x=(w-text_w)/2:y=550:enable='between(t,15,20)',"
                "drawtext=text='1. Property Layout Designer':fontsize=32:fontcolor=00d4ff:"
                "x=200:y=650:enable='between(t,20,30)',"
                "drawtext=text='2. Vastu Shastra Validation':fontsize=32:fontcolor=00d4ff:"
                "x=200:y=700:enable='between(t,20,30)',"
                "drawtext=text='3. Astrology Insights':fontsize=32:fontcolor=00d4ff:"
                "x=200:y=750:enable='between(t,20,30)',"
                "drawtext=text='4. Smart Messaging System':fontsize=32:fontcolor=00d4ff:"
                "x=200:y=800:enable='between(t,20,30)',"
                "drawtext=text='AI-Powered Property Search':fontsize=40:fontcolor=white:"
                "x=(w-text_w)/2:y=300:enable='between(t,30,45)',"
                "drawtext=text='Intelligent Recommendations':fontsize=32:fontcolor=00ff88:"
                "x=200:y=400:enable='between(t,30,45)',"
                "drawtext=text='Advanced Filtering':fontsize=32:fontcolor=00ff88:"
                "x=200:y=450:enable='between(t,30,45)',"
                "drawtext=text='Real-time Updates':fontsize=32:fontcolor=00ff88:"
                "x=200:y=500:enable='between(t,30,45)',"
                "drawtext=text='Vastu Shastra Integration':fontsize=40:fontcolor=white:"
                "x=(w-text_w)/2:y=300:enable='between(t,45,60)',"
                "drawtext=text='8-Direction Analysis':fontsize=32:fontcolor=ff6b6b:"
                "x=200:y=400:enable='between(t,45,60)',"
                "drawtext=text='Energy Flow Optimization':fontsize=32:fontcolor=ff6b6b:"
                "x=200:y=450:enable='between(t,45,60)',"
                "drawtext=text='Personalized Remedies':fontsize=32:fontcolor=ff6b6b:"
                "x=200;y=500:enable='between(t,45,60)',"
                "drawtext=text='Astrology & Birth Charts':fontsize=40:fontcolor=white:"
                "x=(w-text_w)/2:y=300:enable='between(t,60,75)',"
                "drawtext=text='Personalized Predictions':fontsize=32:fontcolor=e91e63:"
                "x=200:y=400:enable='between(t,60,75)',"
                "drawtext=text='Career Guidance':fontsize=32:fontcolor=e91e63:"
                "x=200;y=450:enable='between(t,60,75)',"
                "drawtext=text='Relationship Insights':fontsize=32:fontcolor=e91e63:"
                "x=200;y=500:enable='between(t,60,75)',"
                "drawtext=text='Advanced Chat System':fontsize=40:fontcolor=white:"
                "x=(w-text_w)/2:y=300:enable='between(t,75,90)',"
                "drawtext=text='Real-time Messaging':fontsize=32:fontcolor=4caf50:"
                "x=200;y=400:enable='between(t,75,90)',"
                "drawtext=text='Team Collaboration':fontsize=32:fontcolor=4caf50:"
                "x=200;y=450:enable='between(t,75,90)',"
                "drawtext=text='File Sharing':fontsize=32:fontcolor=4caf50:"
                "x=200;y=500:enable='between(t,75,90)',"
                "drawtext=text='Download PropertyYards Today!':fontsize=48:fontcolor=00ff88:"
                "x=(w-text_w)/2:y=400:enable='between(t,210,240)',"
                "drawtext=text='Available on iOS, Android & Web':fontsize=32:fontcolor=white:"
                "x=(w-text_w)/2:y=460:enable='between(t,210,240)',"
                "drawtext=text='www.propertyyards.com':fontsize=36:fontcolor=00d4ff:"
                "x=(w-text_w)/2;y=520:enable='between(t,210,240)'"
            ),
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-preset', 'fast',
            '-crf', '23',
            str(demo_dir / 'propertyyards_demo_video.mp4')
        ]
        
        print("Generating video with FFmpeg...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("Video created successfully!")
            create_audio(demo_dir)
        else:
            print(f"FFmpeg error: {result.stderr}")
            create_fallback_video(demo_dir)
            
    except FileNotFoundError:
        print("FFmpeg not found. Creating fallback video...")
        create_fallback_video(demo_dir)
    except subprocess.TimeoutExpired:
        print("Video creation timed out. Creating fallback...")
        create_fallback_video(demo_dir)

def create_audio(demo_dir):
    """Create simple audio narration"""
    
    try:
        # Create a simple tone for demo
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', 'sine=frequency=440:duration=240',
            '-af', 'volume=0.1',
            str(demo_dir / 'propertyyards_demo_audio.wav')
        ]
        
        print("Creating audio track...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            combine_video_audio(demo_dir)
        else:
            print(f"Audio creation failed: {result.stderr}")
            
    except Exception as e:
        print(f"Audio creation error: {e}")

def combine_video_audio(demo_dir):
    """Combine video and audio"""
    
    try:
        cmd = [
            'ffmpeg', '-y',
            '-i', str(demo_dir / 'propertyyards_demo_video.mp4'),
            '-i', str(demo_dir / 'propertyyards_demo_audio.wav'),
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-shortest',
            str(demo_dir / 'propertyyards_final_demo.mp4')
        ]
        
        print("Combining video and audio...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Final video with audio created successfully!")
            print(f"Video saved as: {demo_dir / 'propertyyards_final_demo.mp4'}")
            print(f"Duration: 4 minutes")
            print(f"Resolution: 1920x1080")
            print(f"File size: Check the demo folder")
        else:
            print(f"Video combination failed: {result.stderr}")
            
    except Exception as e:
        print(f"Video combination error: {e}")

def create_fallback_video(demo_dir):
    """Create a video info file when FFmpeg is not available"""
    
    video_info = """# PropertyYards Demo Video

## Video Specifications
- **Duration**: 4 minutes
- **Resolution**: 1920x1080 (Full HD)
- **Frame Rate**: 30 FPS
- **Format**: MP4 with H.264 codec
- **Audio**: AAC stereo with narration

## Video Content Timeline

### [0:00-0:05] Opening
- PropertyYards logo and branding
- Platform introduction

### [0:05-0:15] Platform Statistics
- 10,000+ Properties Listed
- 50,000+ Happy Users
- 500 Cr+ Transactions
- 4.9 Star User Rating

### [0:15-0:20] Features Overview
- Introduction to revolutionary features

### [0:20-0:30] Core Features
1. Property Layout Designer
2. Vastu Shastra Validation
3. Astrology Insights
4. Smart Messaging System

### [0:30-0:45] AI-Powered Search
- Intelligent recommendations
- Advanced filtering
- Real-time updates

### [0:45-1:00] Vastu Integration
- 8-direction analysis
- Energy flow optimization
- Personalized remedies

### [1:00-1:15] Astrology Features
- Birth chart analysis
- Personalized predictions
- Career and relationship guidance

### [1:15-1:30] Chat System
- Real-time messaging
- Team collaboration
- File sharing

### [1:30-2:10] Platform Demo
- Property search interface
- Layout designer demo
- Vastu analysis showcase
- Astrology chat demo
- Messaging system

### [2:10-3:30] Advanced Features
- Image upload and processing
- Rewards system
- Analytics dashboard
- Multilingual support

### [3:30-4:00] Call to Action
- Download instructions
- Website information
- Contact details

## Audio Narration Script

### English Version
- Professional voiceover with clear pronunciation
- Background music with Indian classical elements
- Sound effects for interactions

### Multilingual Support
- Hindi narration available
- Spanish and French versions
- Localized content

## Technical Requirements

### To Create the Actual Video:
1. Install FFmpeg: https://ffmpeg.org/download.html
2. Run this script: python simple_video_creator.py
3. Or use professional video editing software

### Professional Production:
- Use Adobe Premiere Pro or Final Cut Pro
- Record professional voiceovers
- Add actual screen recordings
- Include stock footage of properties
- Add professional transitions and effects

## File Locations
- Video: demo/propertyyards_final_demo.mp4
- Script: demo/simple_video_creator.py
- Info: demo/VIDEO_INFO.md

## Next Steps
1. Install FFmpeg for video generation
2. Record professional voiceovers
3. Add actual platform screen recordings
4. Include stock footage and animations
5. Publish on YouTube and other platforms
"""
    
    with open(demo_dir / "VIDEO_INFO.md", 'w') as f:
        f.write(video_info)
    
    print("Video information file created!")
    print("To create the actual video:")
    print("1. Install FFmpeg from https://ffmpeg.org/download.html")
    print("2. Run: python simple_video_creator.py")
    print("3. Or use professional video editing software")

if __name__ == "__main__":
    create_video()
