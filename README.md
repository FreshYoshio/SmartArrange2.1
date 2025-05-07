# Smart Arrange 2.1 - README

## 📂 Overview
SmartArrange 2.1 is a comprehensive desktop application for managing files with a sleek, modern interface. It offers advanced features beyond standard file browsers, including AI-powered organization, duplicate detection, storage analysis, and more.

## ✨ Key Features

### 🗂️ File Management
- Intuitive file browsing with detailed views
- Bulk file operations (rename, delete, organize)
- File previews (images, text, media)
- Advanced search and filtering
- File tagging and notes

### 🧹 Organization Tools
- Automatic file categorization by type
- Duplicate file detection
- Unused file cleaner (files not accessed in 1 year)
- Bulk renaming with patterns

### 📊 Analytics
- Storage usage statistics
- File type distribution visualizations
- Storage growth predictions
- Historical usage tracking

### 🎛️ Customization
- Multiple UI themes (Dark, Light, Ocean, Professional)
- Configurable features
- Responsive interface

## 🛠️ Technical Details

### Requirements
- Python 3.7+
- Required packages:
  ```
  tkinter
  pillow
  numpy
  scikit-learn
  matplotlib
  pygame
  gtts
  ```

### Installation
1. Clone the repository or download the source files
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python file_manager.py
   ```

### File Structure
```
file_manager.py      # Main application file
filemanager_config.json  # Configuration file (auto-generated)
```

## 🚀 Usage

### Basic Navigation
- Use the sidebar for quick access to common folders
- Double-click files to open them
- Right-click for context menu options

### Advanced Features
1. **Organize Files**: Automatically sorts files into categorized folders
2. **Find Duplicates**: Identifies duplicate files by content hash
3. **Clean Unused**: Finds files not accessed in the last year
4. **Bulk Rename**: Rename multiple files using pattern matching
5. **Storage Stats**: View detailed storage analytics and predictions

### Settings
Access settings via the gear icon (⚙️) in the header to:
- Change application theme
- Toggle AI features
- Configure auto-clean options

## 📝 Notes
- The application saves settings automatically to `filemanager_config.json`
- File tags and notes are currently stored in memory (not persisted)
- Some advanced features require additional Python packages

## 📜 License
This project is open-source and available under the MIT License.

## 🤝 Contributing
Contributions are welcome! Please fork the repository and submit pull requests.

---

Enjoy managing your files with Smart Arrange 2.1! 🎉
