# NutriBot - AI-Powered Healthy Diet and Nutrition Assistant

NutriBot is an AI-powered nutrition assistant that provides personalized meal planning, calorie guidance, nutrition tracking, and automated reminder emails.

The system uses:
- **Flask** backend APIs
- **Streamlit** frontend
- **Supabase** for persistence (with local fallback)
- **Groq LLM** for conversational responses and food-text parsing
- **NumPy + ML models** for calorie prediction and meal health scoring
- **Search/Optimization algorithms** (Backtracking, Best-First Search, Knapsack DP)
- **GitHub Actions + Gmail SMTP** for scheduled reminders

## Implemented Features

- User registration and profile storage (height, weight, age, goal, restrictions)
- BMI and daily calorie target calculation
- Personalized macro target calculation
- Chat assistant with persistent chat history
- 7-day meal plan generation with non-repetitive day combinations
- Ingredient-based meal suggestions
- Grocery list generation from latest saved meal plan (automatic, no manual paste required)
- Knapsack-based optimization of grocery priority picks
- Natural-language food logging with calorie/macronutrient estimation
  - USDA-based estimation flow (with fallback)
- Daily/scheduled email nutrition reminders
- ML tools:
  - Daily calorie prediction model
  - Meal health score classifier

## AI/Algorithm Components

### 1) Backtracking Search
- Used for 7-day meal planning.
- Enforces meal-slot constraints and avoids identical full-day repeats.

### 2) Best-First Search
- Used for ranking ingredient-based meal matches.
- Scores by overlap + nutrition heuristic.

### 3) 0/1 Knapsack Dynamic Programming
- Used for grocery optimization.
- Maximizes nutrition score under calorie budget constraints.

### 4) Embedded ML Models (NumPy)
- Linear regression for calorie prediction.
- KNN-style weighted scoring for meal health classification.

## External API Usage

- **Groq API**: chat response generation, structured parsing support.
- **USDA FoodData Central API**: nutrition data lookup for food estimates.
- **Spoonacular API**: ingredient-based recipe suggestions (with fallback to local catalog if unavailable).
- **Supabase**: users, meal plans, nutrition logs, and chat history persistence.

## Project Structure

```text
NutriAI/
├── backend/
│   ├── app.py
│   ├── routes/
│   │   ├── user_routes.py
│   │   ├── chat_routes.py
│   │   ├── meal_routes.py
│   │   └── nutrition_routes.py
│   ├── services/
│   │   ├── bmi_service.py
│   │   ├── ml_service.py
│   │   ├── search_service.py
│   │   ├── notification_service.py
│   │   ├── supabase_service.py
│   │   ├── groq_service.py
│   │   ├── usda_service.py
│   │   └── spoonacular_service.py
│   └── config.py
├── frontend/
│   ├── app.py
│   ├── components/
│   │   ├── api_client.py
│   │   └── ui_helpers.py
│   └── pages/
├── scripts/
│   └── send_scheduled_notifications.py
├── .github/workflows/
│   └── nutrition-reminders.yml
├── tests/
│   ├── test_phase1.py
│   └── test_algorithms_phase2.py
└── requirements.txt
```

## Environment Variables

Create a `.env` file in project root:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_or_service_key

GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant

USDA_KEY=your_usda_api_key
SPOONACULAR_KEY=your_spoonacular_api_key

GMAIL_USER=your_gmail_address
GMAIL_PASS=your_gmail_app_password
```

## Local Run Instructions

Install dependencies:

```bash
pip install -r requirements.txt
```

Run backend:

```bash
python backend/app.py
```

Run frontend:

```bash
streamlit run frontend/app.py
```

## Scheduled Reminder Automation

GitHub Actions workflow:
- File: `.github/workflows/nutrition-reminders.yml`
- Trigger:
  - Cron schedule
  - Manual dispatch
- Sends scheduled reminders by running `scripts/send_scheduled_notifications.py`

Required GitHub Secrets:
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `GMAIL_USER`
- `GMAIL_PASS`

## API Endpoints (Core)

- `POST /api/user/register`
- `GET /api/user/profile`
- `PUT /api/user/update`

- `POST /api/chat/message`
- `GET /api/chat/history`

- `POST /api/meal/generate`
- `GET /api/meal/latest`
- `POST /api/meal/ingredient-suggest`
- `POST /api/meal/grocery-list`
- `POST /api/meal/optimize-grocery`
- `POST /api/meal/ml-predict`
- `POST /api/meal/health-score`

- `POST /api/nutrition/log`
- `GET /api/nutrition/logs`

## Test Commands

```bash
python -m pytest tests/test_phase1.py -q
python -m pytest tests/test_algorithms_phase2.py -q
```

## Notes

- If Supabase is unavailable, local JSON fallback storage is used.
- If Spoonacular is unavailable, ingredient suggestions fallback to local recipe catalog.
- If USDA estimation is unavailable, nutrition log estimation falls back to LLM-formatted estimate.