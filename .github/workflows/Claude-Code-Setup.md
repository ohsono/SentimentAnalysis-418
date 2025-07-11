# Claude Code Integration Setup Guide

This guide helps you set up the Claude Code GitHub Actions workflow with model restrictions to ensure cost-effective usage.

## 🎯 Key Features

- **Model Restriction**: Forces `claude-sonnet-4-20250514` (excludes premium Claude Opus 4)
- **Usage Safeguards**: Token limits and file count restrictions
- **Multiple Triggers**: PRs, pushes, and manual dispatch
- **Comprehensive Analysis**: Code review, security, optimization, testing, documentation
- **Automatic PR Comments**: Results posted directly to pull requests

## 📋 Setup Requirements

### 1. Add GitHub Secrets

Add authentication secrets to GitHub repository (Settings → Secrets and variables → Actions):

**Option 1: Claude Code OAuth Token (Recommended)**
1. Click **New repository secret**
2. Name: `CLAUDE_CODE_OAUTH_TOKEN`
3. Value: Your Claude Code OAuth token

**Option 2: Anthropic API Key (Fallback)**
1. Click **New repository secret**
2. Name: `ANTHROPIC_API_KEY`
3. Value: Your subscription-based Anthropic API key

**Note**: The workflow will use `CLAUDE_CODE_OAUTH_TOKEN` if available, otherwise fall back to `ANTHROPIC_API_KEY`.

### 2. Verify Workflow File

Ensure `.github/workflows/claude-code-integration.yml` exists in your repository.

## 🚀 Usage

### Automatic Triggers

#### Pull Request Analysis
- **Trigger**: Opening/updating PRs to `main`, `staging`, or `dev`
- **Action**: Analyzes only changed files
- **Output**: PR comment with analysis results

#### Push Analysis
- **Trigger**: Pushing to `main`, `staging`, `dev`, or `test-*` branches
- **Action**: Analyzes entire codebase (limited to 50 files)
- **Output**: Workflow artifacts

### Manual Triggers

#### Code Review
```bash
# Via GitHub UI: Actions → Claude Code Integration → Run workflow
# Select: task_type = "code-review"
```

#### Security Analysis
```bash
# Via GitHub UI: Actions → Claude Code Integration → Run workflow
# Select: task_type = "security-analysis"
```

#### Performance Optimization
```bash
# Via GitHub UI: Actions → Claude Code Integration → Run workflow
# Select: task_type = "code-optimization"
```

#### Testing Suggestions
```bash
# Via GitHub UI: Actions → Claude Code Integration → Run workflow
# Select: task_type = "testing-suggestions"
```

#### Documentation Review
```bash
# Via GitHub UI: Actions → Claude Code Integration → Run workflow
# Select: task_type = "documentation-review"
```

#### Custom Analysis
```bash
# Via GitHub UI: Actions → Claude Code Integration → Run workflow
# Select: task_type = "custom-prompt"
# Enter your custom prompt in the custom_prompt field
```

## ⚡ Configuration Options

### Manual Dispatch Parameters

| Parameter | Description | Default | Options |
|-----------|-------------|---------|---------|
| `task_type` | Type of analysis | `code-review` | `code-review`, `security-analysis`, `code-optimization`, `testing-suggestions`, `documentation-review`, `custom-prompt` |
| `custom_prompt` | Custom analysis prompt | `` | Any text |
| `target_files` | Specific files to analyze | `` | Comma-separated file paths |
| `max_tokens` | Token usage limit | `10000` | Number (1-50000) |

### Safety Limits

| Limit | Value | Purpose |
|-------|-------|---------|
| Max tokens per run | 10,000 | Cost control |
| Max files per run | 50 | Performance |
| Model restriction | `claude-sonnet-4-20250514` | Exclude premium models |

## 📊 Analysis Types

### 1. Code Review (Default)
- Security vulnerabilities
- Code quality issues
- Performance bottlenecks
- Bug detection
- Architecture feedback

### 2. Security Analysis
- OWASP vulnerability categories
- Data protection issues
- Access control problems
- Input validation gaps
- Dependency vulnerabilities

### 3. Code Optimization
- Performance improvements
- Memory optimization
- Database query optimization
- Network efficiency
- Refactoring opportunities

### 4. Testing Suggestions
- Test coverage analysis
- Unit test recommendations
- Integration test scenarios
- Edge case identification
- Mock strategy suggestions

### 5. Documentation Review
- Code comment quality
- API documentation
- README improvements
- Architecture documentation
- Missing documentation

## 🔒 Security Best Practices

1. **API Key Management**
   - Use GitHub secrets (never commit keys)
   - Use subscription-based keys only
   - Rotate keys regularly

2. **Model Restrictions**
   - Workflow enforces `claude-sonnet-4-20250514`
   - Premium models (Opus 4) are excluded
   - Usage monitoring tracks model usage

3. **Access Control**
   - Workflow requires `contents: read` permission
   - PR comments require `pull-requests: write`
   - No write access to repository code

## 📈 Usage Monitoring

The workflow automatically logs:
- Model used (`claude-sonnet-4-20250514`)
- Token consumption
- Files analyzed
- Trigger type
- Repository and branch info

## 🛠️ Troubleshooting

### Common Issues

#### "Neither CLAUDE_CODE_OAUTH_TOKEN nor ANTHROPIC_API_KEY secrets are configured"
**Solution**: Add either `CLAUDE_CODE_OAUTH_TOKEN` (preferred) or `ANTHROPIC_API_KEY` to GitHub repository secrets

#### "Too many files changed"
**Solution**: Workflow automatically limits to 50 files for safety

#### "Claude CLI installation failed"
**Solution**: Check GitHub Actions logs for detailed error messages

#### "Model not supported"
**Solution**: Workflow forces `claude-sonnet-4-20250514` - ensure your API key supports this model

### Debug Steps

1. **Check workflow logs** in GitHub Actions tab
2. **Verify authentication** - ensure either `CLAUDE_CODE_OAUTH_TOKEN` or `ANTHROPIC_API_KEY` is set in repository secrets
3. **Test locally** with Claude CLI if needed
4. **Check file permissions** for target files

## 💰 Cost Management

### Cost-Saving Features
- **Model restriction** prevents expensive Opus 4 usage
- **Token limits** cap maximum usage per run
- **File limits** prevent analyzing too many files
- **Smart triggering** only analyzes changed files in PRs

### Usage Optimization
- Use **PR analysis** for incremental review
- Use **manual dispatch** for specific analysis needs
- Set **lower token limits** for quick reviews
- Target **specific files** when possible

## 🔄 Workflow Outputs

### PR Comments
- Analysis results posted automatically
- Truncated if too long (full results in artifacts)
- Includes metadata (model used, file count, etc.)

### Artifacts
- **Full analysis results** (`analysis_result.md`)
- **File list** (`code_files.txt`)
- **30-day retention** period

## 📚 Examples

### Example PR Comment
```markdown
## 🤖 Claude Code Analysis Results

> **Model Used**: `claude-sonnet-4-20250514` (Premium models excluded)
> **Analysis Type**: `code-review`

### Security Issues Found
- **HIGH**: SQL injection vulnerability in user_service.py:45
- **MEDIUM**: Unvalidated input in auth.py:123

### Performance Improvements
- **Optimize database queries** in dashboard.py:67
- **Add caching** for frequently accessed data

### Code Quality
- **Improve error handling** in api_client.py:34
- **Add type hints** to utility functions
```

### Example Custom Prompt
```
Analyze the code for accessibility issues and provide suggestions for improving web accessibility compliance with WCAG 2.1 guidelines.
```

## 🎯 Next Steps

1. **Add authentication** to GitHub secrets (either `CLAUDE_CODE_OAUTH_TOKEN` or `ANTHROPIC_API_KEY`)
2. **Test with a PR** to verify setup
3. **Customize analysis types** based on your needs
4. **Set up regular security scans** using scheduled workflows
5. **Monitor usage** through workflow logs

## 📞 Support

- **GitHub Issues**: Report problems in the repository
- **Workflow Logs**: Check GitHub Actions for detailed error messages
- **Claude Code Docs**: https://docs.anthropic.com/claude-code
- **API Documentation**: https://docs.anthropic.com/api