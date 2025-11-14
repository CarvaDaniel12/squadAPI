# 🚀 Quick Start Guide - Squad Project Generator

## How to Activate and Use the Project Generator

### Step 1: Test the System First (Optional but Recommended)

Run the test to make sure everything works:

```bash
python test_squad_generator.py
```

This will test all components and show you if everything is working correctly.

### Step 2: Use the CLI Commands

**Option A: Generate from Sample Projects**

```bash
# Generate the e-commerce platform example
python -m src.generator.cli generate samples/ecommerce_spec.yaml --output-dir ./my-projects

# Generate the user API example
python -m src.generator.cli generate samples/user_api_spec.yaml --output-dir ./my-projects
```

**Option B: Create from Template**

```bash
# Create a new web app from template
python -m src.generator.cli create my-awesome-app --template web_app --output-dir ./projects

# Create an API service from template
python -m src.generator.cli create my-api-service --template api_service --output-dir ./projects
```

**Option C: List Available Templates**

```bash
python -m src.generator.cli --list-templates
```

### Step 3: Check Your Generated Projects

```bash
# Check what was created
python -m src.generator.cli status ./my-projects/my-awesome-app
```

### Step 4: Access Your Generated Projects

The generated projects will be in the output directory you specified. Each project includes:
- Complete source code
- README with setup instructions
- Deployment guides
- Test files
- Docker configurations

## 🎯 That's It!

Your Squad API is now a **complete software development engine**. Just describe what you want to build and the AI agents will create it for you!

### What Happens When You Run a Command

1. **Specification Parsing**: The system reads your project requirements
2. **AI Planning**: Mary (Architecture Agent) creates the technical plan
3. **Code Generation**: John (Development Agent) builds the actual code
4. **Quality Assurance**: Alex (Quality Agent) creates tests and documentation
5. **Project Packaging**: Everything is organized into a proper project structure
6. **Delivery**: You get a complete, deployable project

### Example: Generate a Blog Platform

```bash
python -m src.generator.cli create my-blog --template web_app --output-dir ./my-projects
```

This creates a complete blog platform with:
- React frontend with blog interface
- Node.js backend with API
- User authentication
- Database setup
- Docker deployment
- Tests and documentation

### Need Help?

- Check `docs/SQUAD_PROJECT_GENERATOR_GUIDE.md` for detailed documentation
- Run the test script to verify everything works
- Look at the sample specifications in the `samples/` folder

**Your Squad is now ready to generate any software project you can imagine!** 🎉
