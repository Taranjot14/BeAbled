from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.optimizers import Adam
import shutil
import os

train_dir = 'processed_data'

# AUTO-CLEAN unwanted system/junk folders
for folder in os.listdir(train_dir):
    folder_path = os.path.join(train_dir, folder)
    if folder.startswith('.') or folder == '__MACOSX':
        print(f"🗑️ Removing junk folder: {folder}")
        shutil.rmtree(folder_path)

# Data augmentation & normalization
datagen = ImageDataGenerator(
    rescale=1./255,
    validation_split=0.2,
    rotation_range=20,
    zoom_range=0.15,
    width_shift_range=0.2,
    height_shift_range=0.2,
    horizontal_flip=True
)

train_gen = datagen.flow_from_directory(
    train_dir,
    target_size=(160, 160),
    batch_size=32,
    class_mode='categorical',
    subset='training'
)

val_gen = datagen.flow_from_directory(
    train_dir,
    target_size=(160, 160),
    batch_size=32,
    class_mode='categorical',
    subset='validation'
)

print("✅ Cleaned classes:", train_gen.class_indices)

# Load MobileNetV2 base
base_model = MobileNetV2(input_shape=(160, 160, 3), include_top=False, weights='imagenet')
base_model.trainable = False

# Custom head
x = base_model.output
x = GlobalAveragePooling2D()(x)
x = Dropout(0.5)(x)
predictions = Dense(train_gen.num_classes, activation='softmax')(x)
model = Model(inputs=base_model.input, outputs=predictions)

model.compile(optimizer=Adam(learning_rate=0.001), loss='categorical_crossentropy', metrics=['accuracy'])
model.fit(train_gen, validation_data=val_gen, epochs=10)
import json

# Save class indices
with open('class_indices.json', 'w') as f:
    json.dump(train_gen.class_indices, f)
print("✅ Saved class_indices.json")

model.save('gesture_mobilenet_advanced2.h5')
print("✅ Model saved as gesture_mobilenet_advanced2.h5")
