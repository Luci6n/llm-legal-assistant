# Legal Assistant Chat Interface

A modern, responsive chat interface for the Intelligent Legal Assistant (ILA) designed for Malaysian Civil Cases.

## 📁 File Structure

```
app/web/
├── index.html          # Main HTML file (clean, semantic structure)
├── styles.css          # All CSS styles and animations
├── script.js           # JavaScript application logic
├── config.json         # Configuration settings
├── README.md           # This documentation file
└── chat_interface.html # Original monolithic file (backup)
```

## 🚀 Features

- **Clean Architecture**: Separated HTML, CSS, and JavaScript for maintainability
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Smooth Animations**: Elegant sidebar transitions and UI interactions
- **File Upload**: Support for documents and images with preview
- **Real-time Chat**: Streaming responses with typing indicators
- **Chat History**: Persistent conversation management
- **Accessibility**: Keyboard navigation and focus management
- **Modern UI**: Claude-inspired dark theme

## 🎨 Styling (styles.css)

### Key Features:
- **Custom CSS variables** for easy theme customization
- **Smooth transitions** for all interactive elements
- **Responsive breakpoints** for mobile optimization
- **Animation keyframes** for enhanced user experience
- **Focus states** for accessibility compliance

### CSS Organization:
```css
/* Base styles and fonts */
/* Scrollbar styling */
/* Material icons */
/* Sidebar animations */
/* Main content transitions */
/* Mobile responsiveness */
/* UI enhancements */
/* Loading states */
```

## 🔧 JavaScript (script.js)

### Architecture:
- **Class-based structure** for better organization
- **Modular methods** for specific functionality
- **Event-driven design** for responsive interactions
- **Async/await patterns** for API calls
- **Error handling** throughout the application

### Key Classes:
```javascript
class LegalAssistantChat {
    constructor()           // Initialize the app
    initializeElements()    // Setup DOM references
    bindEvents()           // Attach event listeners
    initialize()           // App startup logic
    
    // Sidebar management
    closeSidebar()
    openSidebar()
    
    // Chat functionality
    loadChatHistory()
    createNewChat()
    sendMessage()
    
    // File handling
    handleFileUpload()
    uploadFile()
    displayUploadedFile()
    
    // UI utilities
    showStatus()
    hideStatus()
    autoResizeTextarea()
}
```

## ⚙️ Configuration (config.json)

Centralized configuration for easy customization:

- **API endpoints** and base URL
- **Theme colors** and UI settings
- **Feature flags** for enabling/disabling functionality
- **Text content** and error messages
- **File upload** restrictions and settings

## 🎯 Usage

### Basic Setup:
1. Ensure all files are in the same directory
2. Open `index.html` in a web browser
3. The application will automatically initialize

### Development:
```html
<!-- Link to external files -->
<link rel="stylesheet" href="styles.css">
<script src="script.js"></script>
```

### Customization:
1. **Colors**: Modify the Tailwind config in `index.html` or CSS variables in `styles.css`
2. **API**: Update endpoints in `config.json`
3. **Features**: Toggle functionality in the JavaScript configuration
4. **Text**: Update all user-facing text in `config.json`

## 📱 Responsive Design

### Breakpoints:
- **Desktop**: Full sidebar with content margin adjustment
- **Tablet**: Collapsible sidebar with overlay
- **Mobile**: Full-screen overlay sidebar

### Mobile Features:
- Touch-friendly buttons and inputs
- Swipe gestures for sidebar
- Optimized typography and spacing
- Fixed positioning for optimal UX

## 🔐 Security Considerations

- **File upload validation** on both client and server
- **XSS protection** with proper HTML escaping
- **CSRF tokens** for API requests (implement server-side)
- **Content Security Policy** headers recommended

## 🚀 Performance

### Optimizations:
- **Lazy loading** for chat history
- **Debounced input** for auto-resize functionality
- **Efficient DOM manipulation** with minimal reflows
- **CSS animations** using transform for GPU acceleration

## 🧪 Testing

### Browser Support:
- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

### Testing Checklist:
- [ ] Sidebar toggle functionality
- [ ] File upload and preview
- [ ] Message sending and receiving
- [ ] Responsive design on mobile
- [ ] Keyboard navigation
- [ ] Error handling scenarios

## 🔧 Development Guidelines

### Code Style:
- Use **semantic HTML** elements
- Follow **BEM methodology** for CSS classes
- Implement **async/await** for all API calls
- Add **JSDoc comments** for complex functions
- Use **const/let** instead of var

### Performance Tips:
- Minimize DOM queries by caching elements
- Use event delegation for dynamic content
- Implement virtual scrolling for large chat histories
- Optimize images and use WebP format when possible

## 📄 License

This project is part of the Legal Assistant application. All rights reserved.

## 🤝 Contributing

1. Follow the established file structure
2. Maintain separation of concerns (HTML/CSS/JS)
3. Test on multiple browsers and devices
4. Update documentation for any new features
5. Ensure accessibility compliance

---

**Note**: This separated structure makes the codebase much more maintainable and allows for easier debugging, testing, and collaboration.