# Meraki Dashboard HA Documentation

This directory contains the documentation website for the Meraki Dashboard Home Assistant integration, built with Jekyll and hosted on GitHub Pages.

## 🌐 Live Site

The documentation is available at: https://rknightion.github.io/meraki-dashboard-ha

## 📁 Structure

```
docs/
├── _config.yml          # Jekyll configuration
├── _layouts/            # Page layouts
│   └── device.html      # Layout for device pages
├── _devices/            # Device-specific documentation
│   └── mt20.md          # Example device page
├── index.md             # Home page
├── installation.md      # Installation guide
├── configuration.md     # Configuration guide
├── usage.md             # Usage examples and guides
├── troubleshooting.md   # Troubleshooting guide
├── development.md       # Development guide
├── api-reference.md     # Technical API reference
├── faq.md               # Frequently asked questions
├── changelog.md         # Version history
├── 404.md               # 404 error page
├── Gemfile              # Ruby dependencies
└── README.md            # This file
```

## 🚀 Local Development

### Prerequisites

- Ruby 3.1 or higher
- Bundler gem

### Setup

1. **Install dependencies:**
   ```bash
   cd docs
   bundle install
   ```

2. **Run local server:**
   ```bash
   bundle exec jekyll serve
   ```

3. **Open in browser:**
   ```
   http://localhost:4000/meraki-dashboard-ha/
   ```

### Live Reload

Jekyll automatically watches for changes and rebuilds the site. Simply edit files and refresh your browser to see changes.

## ✏️ Contributing to Documentation

### Making Changes

1. **Edit existing pages** - Modify the `.md` files directly
2. **Add new pages** - Create new `.md` files with proper front matter
3. **Update navigation** - Modify `_config.yml` to add pages to navigation

### Front Matter

All pages should include front matter:

```yaml
---
layout: page
title: Page Title
nav_order: 5  # Optional: for navigation ordering
---
```

### Adding Device Documentation

To document a new device:

1. **Create device file** in `_devices/` directory:
   ```yaml
   ---
   layout: device
   title: MT30 Environmental Sensor
   model: MT30
   manufacturer: Cisco Meraki
   categories: [temperature, humidity, co2, tvoc, pm25]
   ---
   ```

2. **Follow the MT20 template** for content structure
3. **Update main pages** to reference the new device

### Writing Guidelines

- **Use clear headings** for easy navigation
- **Include code examples** with proper syntax highlighting
- **Add screenshots** where helpful (store in `assets/images/`)
- **Link between pages** using relative links
- **Test all examples** before documenting
- **Follow existing style** for consistency

### Code Examples

Use fenced code blocks with language specification:

````markdown
```yaml
automation:
  - alias: "Example"
    trigger:
      - platform: state
```
````

### Images

Store images in `assets/images/` and reference them:

```markdown
![Description](assets/images/screenshot.png)
```

## 🔧 Technical Details

### Jekyll Configuration

The site uses:
- **Theme**: Minima
- **Plugins**: Jekyll Feed, Sitemap, SEO Tag
- **Collections**: Devices for device-specific documentation
- **Base URL**: `/meraki-dashboard-ha` for GitHub Pages

### GitHub Actions

The site is automatically built and deployed using GitHub Actions:
- **Trigger**: Push to main branch with changes to `docs/`
- **Build**: Jekyll build with GitHub Pages environment
- **Deploy**: Automatic deployment to GitHub Pages

### SEO & Analytics

- **SEO**: Handled by jekyll-seo-tag plugin
- **Sitemap**: Generated automatically
- **Analytics**: Can be added via Google Analytics ID in `_config.yml`

## 📝 Content Guidelines

### Documentation Principles

1. **User-focused** - Write for users, not developers
2. **Step-by-step** - Provide clear, actionable instructions
3. **Examples** - Include real-world examples and use cases
4. **Current** - Keep information up to date with latest versions
5. **Accessible** - Use clear language and good structure

### Content Types

- **Guides** - Step-by-step tutorials (installation, configuration)
- **Reference** - Technical specifications (API reference)
- **Examples** - Code samples and use cases (usage guide)
- **Troubleshooting** - Problem-solving information
- **FAQ** - Quick answers to common questions

### Maintenance

- **Review regularly** - Keep content current with integration updates
- **Update screenshots** - Refresh UI screenshots when interfaces change
- **Test links** - Verify all internal and external links work
- **Check examples** - Ensure code examples still work

## 🚀 Deployment

### Automatic Deployment

Changes to the `docs/` directory on the main branch trigger automatic deployment:

1. **GitHub Actions** builds the Jekyll site
2. **Artifacts** are uploaded to GitHub Pages
3. **Site updates** are live within minutes

### Manual Deployment

If needed, you can manually trigger deployment:

1. Go to **Actions** tab in GitHub repository
2. Select **Deploy GitHub Pages** workflow
3. Click **Run workflow** → **Run workflow**

## 🤝 Getting Help

### Documentation Issues

- **Bug reports** - File issues on GitHub
- **Content requests** - Use GitHub discussions
- **Pull requests** - For direct contributions

### Questions

- **GitHub Issues** - For bugs or missing content
- **GitHub Discussions** - For questions and ideas
- **Review existing docs** - Check if information already exists

---

**Ready to contribute?** Start by improving existing content or adding examples from your own usage! 