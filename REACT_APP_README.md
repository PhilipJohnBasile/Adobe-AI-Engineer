# 🥤 Coca-Cola Campaign Manager

A modern React application for managing creative automation campaigns with built-in brand compliance and legal validation.

## 🚀 Features

### Campaign Management
- **Create** new campaigns with guided forms
- **Edit** existing campaigns with real-time validation
- **Delete** campaigns with confirmation
- **View** detailed campaign information and analytics

### AI-Powered Tools
- **Campaign Idea Generation** - AI suggestions for new campaigns
- **Content Validation** - Real-time brand compliance checking
- **Pipeline Integration** - One-click asset generation

### Brand Compliance & Legal Checks
- **Brand Guidelines Enforcement** - Coca-Cola red (#DA020E), logo placement, typography
- **Forbidden Words Detection** - Competitor names, inappropriate content
- **Regional Compliance** - Cultural sensitivity validation
- **Compliance Scoring** - Automated scoring with detailed reports

### Asset Generation
- **Multi-Format Output** - Square (1:1), Story (9:16), Landscape (16:9)
- **Cultural Localization** - USA, Germany, Japan market adaptation
- **Real-time Processing** - Live pipeline execution with progress tracking
- **Comprehensive Reporting** - Detailed logs and analytics

## 🛠 Technology Stack

- **Frontend**: React 18 + TypeScript
- **UI Framework**: Tailwind CSS with custom Coca-Cola branding
- **State Management**: React Hooks
- **API Integration**: Axios for REST communication
- **Icons**: Lucide React
- **Backend**: Node.js + Express
- **Pipeline**: Python integration

## 📦 Installation & Setup

### Prerequisites
- Node.js 14+
- Python 3.8+
- npm or yarn

### Backend Setup
```bash
# Install backend dependencies
cd task2
npm install

# Start the backend server
npm start
# Server runs on http://localhost:3001
```

### Frontend Setup
```bash
# Install frontend dependencies
cd task2/campaign-manager
npm install

# Start the React development server
npm start
# App runs on http://localhost:3000
```

### Quick Start (Both Services)
```bash
# Terminal 1: Start backend
cd task2
npm start

# Terminal 2: Start frontend
cd task2/campaign-manager
npm start
```

## 🎯 Usage Guide

### Creating a New Campaign

1. **Click "New Campaign"** from the main dashboard
2. **Fill Campaign Details** - Name, dates, client information
3. **Add Campaign Message** - Headlines, brand voice, seasonal themes
4. **Configure Products** - Add products with descriptions and benefits
5. **Set Target Regions** - Define markets with cultural notes
6. **Generate Ideas** (Optional) - Use AI to suggest campaign concepts
7. **Validate Campaign** - Run compliance and legal checks
8. **Save Campaign** - Store for future use and asset generation

### Running the Pipeline

1. **Select Campaign** from the list
2. **Click "Run Pipeline"** button
3. **Monitor Progress** - Real-time status updates
4. **View Results** - Generated assets and reports

### Compliance Validation

The app automatically validates:
- **Brand Colors** - Ensures Coca-Cola red (#DA020E) usage
- **Logo Placement** - Validates brand guideline compliance
- **Content Review** - Scans for prohibited words
- **Cultural Sensitivity** - Regional appropriateness checks

## 🏗 Architecture

### Frontend Components
```
src/
├── components/
│   ├── CampaignList.tsx      # Main campaign dashboard
│   ├── CampaignForm.tsx      # Create/edit campaigns
│   ├── CampaignDetail.tsx    # Detailed campaign view
│   └── ...
├── services/
│   ├── CampaignService.ts    # API communication
│   └── ComplianceService.ts  # Validation logic
├── types/
│   └── Campaign.ts           # TypeScript definitions
└── App.tsx                   # Main application
```

### Backend API Endpoints
```
GET    /api/campaigns          # List all campaigns
GET    /api/campaigns/:id      # Get specific campaign
POST   /api/campaigns          # Create new campaign
PUT    /api/campaigns/:id      # Update campaign
DELETE /api/campaigns/:id      # Delete campaign
POST   /api/campaigns/generate # Generate AI ideas
POST   /api/campaigns/validate # Validate compliance
POST   /api/campaigns/:id/generate # Run pipeline
GET    /api/campaigns/:id/logs # Get generation logs
```

## 🎨 Branding & Design

### Color Palette
- **Coca-Cola Red**: #DA020E (Primary brand color)
- **Sprite Green**: #00A651 (Product accent)
- **Fanta Orange**: #FF8C00 (Product accent)

### Typography
- **Headlines**: Spencerian Script (brand standard)
- **Body Text**: Gotham (readable, modern)
- **UI Elements**: System fonts for performance

### Custom Components
- Coca-Cola branded header with logo
- Custom form inputs with brand focus styles
- Compliance status indicators
- Pipeline progress animations

## 🔧 Configuration

### Environment Variables
Create `.env` in the backend root:
```
OPENAI_API_KEY=your_openai_key_here
ADOBE_API_KEY=your_adobe_key_here
PORT=3001
```

### Brand Guidelines
Modify `assets/brand/guidelines.json` to customize:
- Color requirements
- Logo placement rules
- Typography standards
- Messaging guidelines

### Compliance Rules
Update `assets/brand/compliance.json` for:
- Forbidden words lists
- Regional restrictions
- Content policies
- Validation thresholds

## 📊 Features in Detail

### Real-time Validation
- **Live Feedback** - Form validation as you type
- **Visual Indicators** - Color-coded compliance status
- **Detailed Reports** - Specific issues and recommendations
- **Score Tracking** - Percentage-based compliance scoring

### AI Integration
- **Campaign Ideas** - OpenAI-powered concept generation
- **Content Suggestions** - Contextual messaging recommendations
- **Cultural Adaptation** - Region-specific content optimization

### Pipeline Integration
- **One-click Generation** - Direct Python pipeline execution
- **Progress Monitoring** - Real-time status updates
- **Result Visualization** - Generated asset previews
- **Log Management** - Detailed execution reports

## 🚀 Production Deployment

### Build for Production
```bash
# Build React app
cd campaign-manager
npm run build

# Serve with backend
cd ..
npm start
```

### Docker Deployment
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY . .
EXPOSE 3001
CMD ["npm", "start"]
```

## 🔍 Testing

### Manual Testing
1. **Create Campaign** - Fill all required fields
2. **Validation** - Test compliance checks
3. **Pipeline** - Run asset generation
4. **CRUD Operations** - Create, read, update, delete

### Compliance Testing
- Try forbidden words (should fail validation)
- Use wrong colors (should show warnings)
- Test regional restrictions

## 📈 Performance

### Optimization Features
- **Lazy Loading** - Components load on demand
- **Caching** - API responses cached locally
- **Compression** - Gzipped assets for faster loading
- **Code Splitting** - Reduced bundle sizes

### Monitoring
- **Error Tracking** - Console logging for debugging
- **Performance Metrics** - Load time monitoring
- **User Analytics** - Usage pattern tracking

## 🤝 Contributing

### Development Guidelines
1. **Follow TypeScript** - Strict typing for reliability
2. **Use Tailwind** - Consistent styling with utility classes
3. **Brand Compliance** - Always use approved colors and fonts
4. **Test Thoroughly** - Validate all compliance features

### Code Style
- ES6+ syntax
- Functional components with hooks
- Descriptive variable names
- Comprehensive error handling

---

**Built for Adobe AI Engineer Interview Demo**
*Showcasing enterprise-grade creative automation with React and modern web technologies*