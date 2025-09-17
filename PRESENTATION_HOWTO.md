# How to Create HTML Presentation from Markdown

## Quick Start: Using Existing HTML Template

The repository already includes a presentation HTML file at `/Presentation.html`. To update it with the new 60-minute presentation:

1. **Copy the existing template:**
```bash
cp Presentation.html slides/PRESENTATION_60min.html
```

2. **Update the content** with the markdown from `PRESENTATION_60min.md`

## Option 1: Using Marp (Recommended)

Marp is a Markdown presentation ecosystem that creates beautiful slide decks.

### Installation
```bash
# Install via npm
npm install -g @marp-team/marp-cli

# Or via Homebrew (macOS)
brew install marp-cli
```

### Convert to HTML
```bash
# Basic conversion
marp slides/PRESENTATION_60min.md -o slides/PRESENTATION_60min.html

# With theme and options
marp slides/PRESENTATION_60min.md \
  --html \
  --theme-set ./themes/ \
  --pdf-notes \
  -o slides/PRESENTATION_60min.html
```

### Add to Markdown Header
```markdown
---
marp: true
theme: default
paginate: true
backgroundColor: #fff
---
```

## Option 2: Using Reveal.js

### Quick Setup
```bash
# Clone reveal.js
git clone https://github.com/hakimel/reveal.js.git slides/reveal

# Copy presentation
cp slides/PRESENTATION_60min.md slides/reveal/presentation.md

# Install dependencies
cd slides/reveal
npm install
```

### Create HTML Wrapper
Create `slides/PRESENTATION_60min_reveal.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.3.1/reveal.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.3.1/theme/white.min.css">
    <title>Creative Automation Platform - 60 Minute Presentation</title>
</head>
<body>
    <div class="reveal">
        <div class="slides">
            <!-- Slides will be loaded here from markdown -->
        </div>
    </div>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.3.1/reveal.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.3.1/plugin/markdown/markdown.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.3.1/plugin/notes/notes.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.3.1/plugin/highlight/highlight.min.js"></script>
    
    <script>
        Reveal.initialize({
            hash: true,
            slideNumber: true,
            showNotes: false,
            transition: 'slide',
            plugins: [ RevealMarkdown, RevealNotes, RevealHighlight ]
        });
        
        // Load markdown
        fetch('PRESENTATION_60min.md')
            .then(response => response.text())
            .then(markdown => {
                document.querySelector('.slides').innerHTML = 
                    '<section data-markdown data-separator="^---$">' +
                    '<textarea data-template>' + markdown + '</textarea>' +
                    '</section>';
                Reveal.sync();
            });
    </script>
</body>
</html>
```

## Option 3: Using Pandoc

### Installation
```bash
# macOS
brew install pandoc

# Linux
sudo apt-get install pandoc

# Windows
# Download from https://pandoc.org/installing.html
```

### Convert to HTML Slides
```bash
# Slidy format
pandoc -t slidy -s slides/PRESENTATION_60min.md -o slides/PRESENTATION_60min_slidy.html

# RevealJS format
pandoc -t revealjs -s slides/PRESENTATION_60min.md -o slides/PRESENTATION_60min_reveal.html

# DZSlides format
pandoc -t dzslides -s slides/PRESENTATION_60min.md -o slides/PRESENTATION_60min_dzslides.html

# With custom CSS
pandoc -t slidy -s --css=custom.css slides/PRESENTATION_60min.md -o slides/PRESENTATION_60min.html
```

## Option 4: Simple HTML Template

Create a standalone HTML file `slides/PRESENTATION_60min_simple.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Creative Automation Platform - 60 Minute Presentation</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            overflow: hidden;
        }
        .slides-container {
            height: 100vh;
            overflow-y: scroll;
            scroll-snap-type: y mandatory;
        }
        .slide {
            min-height: 100vh;
            scroll-snap-align: start;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 2rem;
            background: white;
            margin: 20px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        h1 { font-size: 3rem; margin-bottom: 1rem; color: #667eea; }
        h2 { font-size: 2rem; margin-bottom: 1rem; color: #764ba2; }
        h3 { font-size: 1.5rem; margin-bottom: 0.5rem; }
        ul { list-style-position: inside; max-width: 800px; }
        li { margin: 0.5rem 0; font-size: 1.2rem; }
        code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
        pre {
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 1rem;
            border-radius: 5px;
            overflow-x: auto;
            max-width: 90%;
            margin: 1rem 0;
        }
        table {
            border-collapse: collapse;
            margin: 1rem 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 0.5rem 1rem;
            text-align: left;
        }
        th { background: #f4f4f4; }
        .slide-number {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(0,0,0,0.1);
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 0.9rem;
        }
        .controls {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 10px;
        }
        button {
            padding: 10px 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1rem;
        }
        button:hover {
            background: #764ba2;
        }
        .speaker-notes {
            display: none;
            background: #fffacd;
            padding: 1rem;
            margin-top: 1rem;
            border-radius: 5px;
            font-style: italic;
        }
        .show-notes .speaker-notes {
            display: block;
        }
    </style>
</head>
<body>
    <div class="slides-container" id="slides">
        <!-- Slides will be inserted here -->
    </div>
    
    <div class="slide-number" id="slideNumber">1 / 40</div>
    
    <div class="controls">
        <button onclick="previousSlide()">← Previous</button>
        <button onclick="toggleNotes()">Toggle Notes</button>
        <button onclick="nextSlide()">Next →</button>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script>
        let currentSlide = 0;
        let slides = [];
        let showNotes = false;
        
        // Load and parse markdown
        fetch('PRESENTATION_60min.md')
            .then(response => response.text())
            .then(markdown => {
                // Split by slide separator
                const slideContents = markdown.split(/^---$/m);
                
                slideContents.forEach((content, index) => {
                    if (content.trim()) {
                        const slideDiv = document.createElement('div');
                        slideDiv.className = 'slide';
                        slideDiv.id = `slide-${index}`;
                        
                        // Separate speaker notes
                        const parts = content.split('**Speaker Notes:**');
                        slideDiv.innerHTML = marked.parse(parts[0]);
                        
                        if (parts[1]) {
                            const notesDiv = document.createElement('div');
                            notesDiv.className = 'speaker-notes';
                            notesDiv.innerHTML = marked.parse(parts[1]);
                            slideDiv.appendChild(notesDiv);
                        }
                        
                        document.getElementById('slides').appendChild(slideDiv);
                        slides.push(slideDiv);
                    }
                });
                
                updateSlideNumber();
                showSlide(0);
            });
        
        function showSlide(n) {
            if (n >= 0 && n < slides.length) {
                currentSlide = n;
                slides[n].scrollIntoView({ behavior: 'smooth' });
                updateSlideNumber();
            }
        }
        
        function nextSlide() {
            showSlide(currentSlide + 1);
        }
        
        function previousSlide() {
            showSlide(currentSlide - 1);
        }
        
        function toggleNotes() {
            showNotes = !showNotes;
            document.body.classList.toggle('show-notes');
        }
        
        function updateSlideNumber() {
            document.getElementById('slideNumber').textContent = 
                `${currentSlide + 1} / ${slides.length}`;
        }
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            switch(e.key) {
                case 'ArrowRight':
                case ' ':
                    nextSlide();
                    break;
                case 'ArrowLeft':
                    previousSlide();
                    break;
                case 'n':
                    toggleNotes();
                    break;
                case 'f':
                    document.documentElement.requestFullscreen();
                    break;
                case 'Escape':
                    document.exitFullscreen();
                    break;
            }
        });
    </script>
</body>
</html>
```

## Option 5: Using Python Present

### Installation
```bash
pip install present
```

### Create Presentation
```python
# create_presentation.py
import present

with open('slides/PRESENTATION_60min.md', 'r') as f:
    markdown = f.read()

present.export_html(
    markdown,
    output='slides/PRESENTATION_60min.html',
    theme='dark',
    code_theme='monokai'
)
```

## Viewing the Presentation

### Local Server (Recommended)
```bash
# Python 3
cd slides
python3 -m http.server 8080

# Node.js
npx http-server slides -p 8080

# Then open: http://localhost:8080/PRESENTATION_60min.html
```

### Direct File Opening
```bash
# macOS
open slides/PRESENTATION_60min.html

# Linux
xdg-open slides/PRESENTATION_60min.html

# Windows
start slides/PRESENTATION_60min.html
```

## Presentation Controls

### Keyboard Shortcuts
- **→** or **Space**: Next slide
- **←**: Previous slide
- **F**: Fullscreen
- **ESC**: Exit fullscreen
- **N**: Toggle speaker notes
- **S**: Show speaker view
- **?**: Show help

## Customization Tips

### Adding Custom CSS
```css
/* custom.css */
.slide {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.slide h1 {
    background: linear-gradient(45deg, #f093fb 0%, #f5576c 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

code {
    background: #282c34;
    color: #abb2bf;
    padding: 2px 6px;
    border-radius: 3px;
}
```

### Adding Animations
```css
@keyframes slideIn {
    from { opacity: 0; transform: translateY(30px); }
    to { opacity: 1; transform: translateY(0); }
}

.slide {
    animation: slideIn 0.5s ease-out;
}
```

## Quick Demo Script

```bash
# 1. Generate HTML from markdown
marp slides/PRESENTATION_60min.md -o slides/PRESENTATION_60min.html

# 2. Start local server
cd slides
python3 -m http.server 8080 &

# 3. Open in browser
open http://localhost:8080/PRESENTATION_60min.html

# 4. Enter fullscreen (press F key)
```

## Troubleshooting

### Mermaid Diagrams Not Rendering
Add mermaid support:
```html
<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
<script>mermaid.initialize({ startOnLoad: true });</script>
```

### Code Highlighting Not Working
Add highlight.js:
```html
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/github.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
<script>hljs.highlightAll();</script>
```

### Images Not Loading
Ensure relative paths are correct:
```markdown
![Image](../assets/image.png)  <!-- Adjust path as needed -->
```

## Final Notes

- Test the presentation before the actual meeting
- Have a PDF backup: `marp slides/PRESENTATION_60min.md --pdf`
- Practice with the timer to ensure 60-minute duration
- Test on the actual presentation hardware/setup if possible