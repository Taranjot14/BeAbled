# BeAbled
SignLanguage Recgnition For Zoom

# Dataset Preprocessing
##  Step 1: Download the Dataset

1. **Access How2Sign Dataset:**
- On the website.
- Download RGB Videos & Transcriptions

##  Step 2: Filter for Specific Phrases

1. **Define Your Phrases:**
   Example:
   - "Can you hear me?"
   - "Please mute your mic."
   - "I have a question."

2. **Match Transcriptions:**
   - Load transcription files.
   - Filter videos that match your phrases.

---

##  Step 3: Extract and Preprocess Video Frames

- Arrange them in the format below

     ```
   dataset/
   ├── can_you_hear_me/
   │   ├── frame1.jpg
   │   ├── frame2.jpg
   ├── please_mute_your_mic/
   │   ├── frame1.jpg
   │   ├── frame2.jpg
   ```

##  Step 4: Prepare Labels

1. **Assign Labels to Phrases:**
   ```
   can_you_hear_me → 0
   please_mute_your_mic → 1
   i_have_a_question → 2
   ```

2. **Create labels.csv:**
   ```
   frame_path,label
   dataset/can_you_hear_me/frame1.jpg,0
   dataset/please_mute_your_mic/frame2.jpg,1
   ```

---

##  Step 5: Now we can start the preparation for training the model

