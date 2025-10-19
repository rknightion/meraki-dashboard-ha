# Translation Guide for Meraki Dashboard Integration

This guide provides detailed instructions for translating the Meraki Dashboard Home Assistant integration into other languages.

## Overview

The integration uses Home Assistant's translation system, which relies on JSON files in the `translations/` directory. Each language has its own JSON file (e.g., `en.json` for English, `fr.json` for French, `de.json` for German).

## Translation Files

### File Locations

- **Source English translations**: `custom_components/meraki_dashboard/translations/en.json`
- **New language translations**: `custom_components/meraki_dashboard/translations/<language_code>.json`
- **Fallback file**: `custom_components/meraki_dashboard/strings.json` (must match `en.json`)

### Language Codes

Use the ISO 639-1 two-letter language codes:

- English: `en`
- French: `fr`
- German: `de`
- Spanish: `es`
- Italian: `it`
- Portuguese: `pt`
- Dutch: `nl`
- Polish: `pl`
- Russian: `ru`
- Chinese (Simplified): `zh-Hans`
- Chinese (Traditional): `zh-Hant`
- Japanese: `ja`
- Korean: `ko`

Full list: https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes

## Creating a New Translation

### Step 1: Copy the English Template

```bash
cd custom_components/meraki_dashboard/translations/
cp en.json <language_code>.json
```

For example, to create a French translation:

```bash
cp en.json fr.json
```

### Step 2: Translate All Text Values

Open your new language file and translate **only the text values**, not the keys.

**Important Rules:**

1. **DO NOT translate JSON keys** - Only translate the values (text after the `:`)
2. **Preserve all placeholders** - Keep variables like `{hub_list}`, `{device_count}`, `{config_entry_title}` unchanged
3. **Maintain formatting** - Keep markdown formatting (`**bold**`, bullet points, line breaks)
4. **Preserve technical terms** - Keep API, SDK, URLs, and technical acronyms in English or appropriate technical translation

### Example

**English (`en.json`):**
```json
{
  "config": {
    "step": {
      "user": {
        "title": "Meraki Dashboard Integration",
        "description": "Connect your Cisco Meraki Dashboard to Home Assistant.\n\n**You will need:**\n• An API key\n• Your Organization ID",
        "data": {
          "api_key": "API Key",
          "organization_id": "Organization ID"
        }
      }
    }
  }
}
```

**French (`fr.json`):**
```json
{
  "config": {
    "step": {
      "user": {
        "title": "Intégration Meraki Dashboard",
        "description": "Connectez votre Cisco Meraki Dashboard à Home Assistant.\n\n**Vous aurez besoin de:**\n• Une clé API\n• Votre ID d'organisation",
        "data": {
          "api_key": "Clé API",
          "organization_id": "ID de l'organisation"
        }
      }
    }
  }
}
```

## Translation Checklist

Use this checklist to ensure complete translation:

### Configuration Flow (`config` section)

- [ ] `config.step.user` - Initial setup screen
  - [ ] Title
  - [ ] Description
  - [ ] All field labels (`data`)
  - [ ] All field descriptions (`data_description`)

- [ ] `config.step.organization` - Organization selection
  - [ ] Title
  - [ ] Description
  - [ ] Field labels
  - [ ] Field descriptions

- [ ] `config.step.device_selection` - Device configuration
  - [ ] Title
  - [ ] Description
  - [ ] Field labels (7 fields)
  - [ ] Field descriptions (7 descriptions)

- [ ] `config.step.reauth` - Re-authentication screen
  - [ ] Title
  - [ ] Description
  - [ ] Field labels
  - [ ] Field descriptions

- [ ] `config.error` - Error messages (5 messages)
  - [ ] `invalid_auth`
  - [ ] `invalid_organization`
  - [ ] `cannot_connect`
  - [ ] `unknown`

- [ ] `config.abort` - Completion messages (3 messages)
  - [ ] `already_configured`
  - [ ] `reauth_successful`
  - [ ] `api_key_updated`

### Options Flow (`options` section)

- [ ] `options.step.init` - Main options screen
  - [ ] Title
  - [ ] Description (includes MT15/MT40 explanation)
  - [ ] Field labels (14 fields)
  - [ ] Field descriptions (11 descriptions)

- [ ] `options.step.api_key` - API key update
  - [ ] Title
  - [ ] Description
  - [ ] Field labels
  - [ ] Field descriptions

- [ ] `options.step.hub_intervals` - Network configuration
  - [ ] Title
  - [ ] Description
  - [ ] Field labels (3 fields)
  - [ ] Field descriptions (3 descriptions)

- [ ] `options.error` - Error messages (5 messages)
- [ ] `options.abort` - Completion messages (1 message)

### Issues & Services

- [ ] `issues` - Issue notifications (3 types)
  - [ ] `api_key_expired`
  - [ ] `network_access_lost`
  - [ ] `device_discovery_failed`

- [ ] `services` - Service descriptions (4 services)
  - [ ] `update_hub_data`
  - [ ] `discover_devices`
  - [ ] `update_all_hubs`
  - [ ] `discover_all_devices`

## Important Placeholders

These placeholders are dynamically replaced at runtime. **Never translate them:**

- `{hub_list}` - List of configured networks
- `{hub_settings_explanation}` - Network settings explanation
- `{device_count}` - Number of devices found
- `{config_entry_title}` - Integration name
- `{network_name}` - Network name
- `{hub_name}` - Hub identifier
- `{organization_name}` - Organization name

## Technical Terms

### Keep These Terms Consistent

**Product Names** (do not translate):
- Meraki Dashboard
- Home Assistant
- Cisco Meraki
- MT (Environmental Sensors)
- MR (Wireless Access Points)
- MS (Switches)
- MT15, MT40 (sensor models)

**Technical Terms** (translate appropriately for your language):
- API Key → Clé API (French), API-Schlüssel (German)
- Organization → Organisation (French), Organisation (German)
- Network → Réseau (French), Netzwerk (German)
- Device → Appareil (French), Gerät (German)
- Sensor → Capteur (French), Sensor (German)
- Auto-Discovery → Découverte automatique (French), Automatische Erkennung (German)
- Update Interval → Intervalle de mise à jour (French), Aktualisierungsintervall (German)

**URLs and Paths** (never translate):
- `https://api.meraki.com/api/v1`
- `https://dashboard.meraki.com/o/XXXXX`
- Organization > Settings > Dashboard API access

## Formatting Preservation

### Markdown

Markdown formatting must be preserved:

```json
"**Bold Text**" → "**Texte en Gras**"
"• Bullet point" → "• Point de liste"
"\n\n" → "\n\n" (line breaks must be preserved exactly)
```

### Unit Labels

Units are often appended to field labels in parentheses:

```json
"Update Interval (minutes)" → "Intervalle de mise à jour (minutes)"
"MT Refresh Interval (seconds)" → "Intervalle de rafraîchissement MT (secondes)"
```

## Validation

After creating your translation, validate it:

### 1. JSON Syntax Check

```bash
python3 -m json.tool custom_components/meraki_dashboard/translations/<language_code>.json
```

This should output the formatted JSON without errors.

### 2. Structure Validation

Ensure your translation file has the exact same structure as `en.json`:

```bash
# Compare structure (keys only)
python3 -c "import json; en = json.load(open('en.json')); lang = json.load(open('<language_code>.json')); print('Keys match:', set(str(en.keys())) == set(str(lang.keys())))"
```

### 3. Placeholder Check

Verify all placeholders are present:

```bash
# Check for missing placeholders
grep -r "{.*}" en.json > en_placeholders.txt
grep -r "{.*}" <language_code>.json > lang_placeholders.txt
diff en_placeholders.txt lang_placeholders.txt
```

If there are differences, ensure you haven't accidentally translated or removed placeholders.

## Testing Your Translation

### 1. Copy to Home Assistant

Copy your translation file to your Home Assistant installation:

```bash
# Development environment
cp <language_code>.json /path/to/homeassistant/custom_components/meraki_dashboard/translations/

# HACS installation
cp <language_code>.json ~/.homeassistant/custom_components/meraki_dashboard/translations/
```

### 2. Change Home Assistant Language

1. Navigate to **Settings** → **System** → **General**
2. Change **Language** to your translated language
3. **Restart Home Assistant**

### 3. Test Configuration Flow

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Meraki Dashboard"
4. Verify all text appears in your language
5. Check for:
   - Proper text rendering
   - No missing translations (English fallback)
   - Correct formatting
   - Proper use of plurals (if applicable)

### 4. Test Options Flow

1. Open an existing Meraki Dashboard integration
2. Click **Configure**
3. Verify options screen text is translated
4. Test error messages (enter invalid API key)

## Common Translation Mistakes

### 1. Translating JSON Keys ❌

```json
// WRONG
"donnees": {
  "api_key": "Clé API"
}

// CORRECT
"data": {
  "api_key": "Clé API"
}
```

### 2. Translating Placeholders ❌

```json
// WRONG
"description": "Trouvé {nombre_appareils} appareil(s)"

// CORRECT
"description": "Trouvé {device_count} appareil(s)"
```

### 3. Breaking Markdown ❌

```json
// WRONG
"description": "* *Texte en gras* *"

// CORRECT
"description": "**Texte en gras**"
```

### 4. Missing Line Breaks ❌

```json
// WRONG
"description": "Line one Line two"

// CORRECT
"description": "Line one\n\nLine two"
```

### 5. Inconsistent Terminology ❌

Don't translate "API" as different terms throughout the file. Pick one translation and use it consistently.

## Contributing Your Translation

### Submit to Project

1. Fork the repository
2. Create a new branch: `git checkout -b translation/<language_code>`
3. Add your translation file
4. Commit: `git commit -m "Add <language_name> translation"`
5. Push: `git push origin translation/<language_code>`
6. Open a Pull Request

### Translation Metadata

Include this information in your PR:

- Language name (English and native)
- Language code (ISO 639-1)
- Your name or username (for credits)
- Any special considerations for your translation

## Quality Assurance

Before submitting:

- [ ] JSON is valid (no syntax errors)
- [ ] All keys from `en.json` are present
- [ ] All placeholders are preserved
- [ ] Markdown formatting is intact
- [ ] Technical terms are consistent
- [ ] Tested in Home Assistant
- [ ] No untranslated English text (except technical terms)
- [ ] Natural phrasing for native speakers

## Getting Help

If you need help with translation:

1. **Check existing translations** - Look at other language files for examples
2. **Home Assistant Translations** - Reference official Home Assistant translations
3. **Ask the community** - Open a GitHub Discussion for translation questions
4. **Review documentation** - Home Assistant translation guidelines

## Maintenance

Translations may need updates when:

- New features are added
- Field descriptions change
- Error messages are improved
- New configuration options are added

### Update Process

1. Compare `en.json` with your translation file
2. Identify new or changed keys
3. Add translations for new keys
4. Update changed descriptions
5. Test the updated translation
6. Submit a PR with updates

## Language-Specific Notes

### Pluralization

Some languages have complex plural rules. Home Assistant supports ICU message format for plurals:

```json
"description": "{device_count, plural, =0 {No devices} =1 {One device} other {# devices}}"
```

Consult Home Assistant's internationalization docs for advanced features.

### Right-to-Left (RTL) Languages

For RTL languages (Arabic, Hebrew, etc.):

- JSON structure stays the same
- Text is written in RTL
- Markdown bullets may need adjustment
- Test carefully in Home Assistant

### Character Encoding

All translation files must be UTF-8 encoded. Most modern editors default to UTF-8, but verify:

```bash
file -I <language_code>.json
```

Should output: `charset=utf-8`

## Example: Full Translation Workflow

### Creating a Spanish Translation

```bash
# 1. Navigate to translations directory
cd custom_components/meraki_dashboard/translations/

# 2. Copy English template
cp en.json es.json

# 3. Edit es.json and translate all text values
# (Use your preferred text editor)

# 4. Validate JSON
python3 -m json.tool es.json > /dev/null && echo "Valid JSON"

# 5. Check structure
diff <(jq -S 'paths | join(".")' en.json) <(jq -S 'paths | join(".")' es.json)

# 6. Copy to Home Assistant
cp es.json ~/.homeassistant/custom_components/meraki_dashboard/translations/

# 7. Change Home Assistant to Spanish and restart

# 8. Test the integration

# 9. Submit PR if everything works
```

## Resources

- **Home Assistant Translations**: https://developers.home-assistant.io/docs/internationalization
- **JSON Validator**: https://jsonlint.com/
- **Markdown Guide**: https://www.markdownguide.org/basic-syntax/
- **ISO Language Codes**: https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes

## Contact

For translation questions or issues:

- Open a GitHub Issue
- Start a GitHub Discussion
- Check existing translations for examples

Thank you for helping make the Meraki Dashboard integration accessible to users worldwide!
