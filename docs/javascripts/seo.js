/* SEO enhancements for Meraki Dashboard Home Assistant Integration */

const SITE = {
  name: 'Meraki Dashboard Home Assistant Integration',
  description: 'Monitor Cisco Meraki environmental sensors, Wi-Fi, and switch infrastructure directly in Home Assistant.',
  url: 'https://m7kni.io/meraki-dashboard-ha/',
  image: 'https://m7kni.io/meraki-dashboard-ha/assets/social-card.png',
  twitter: '@rknightion',
};

document.addEventListener('DOMContentLoaded', function() {
  addStructuredData();
  enhanceMetaTags();
  addOpenGraphTags();
  addTwitterCardTags();
  addCanonicalURL();
});

function addStructuredData() {
  const structuredData = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: SITE.name,
    applicationCategory: 'Home Automation Software',
    operatingSystem: 'Home Assistant',
    description: SITE.description,
    url: SITE.url,
    downloadUrl: 'https://github.com/rknightion/meraki-dashboard-ha',
    softwareVersion: 'latest',
    programmingLanguage: 'Python',
    license: 'https://github.com/rknightion/meraki-dashboard-ha/blob/main/LICENSE',
    author: {
      '@type': 'Person',
      name: 'Rob Knighton',
      url: 'https://github.com/rknightion',
    },
    maintainer: {
      '@type': 'Person',
      name: 'Rob Knighton',
      url: 'https://github.com/rknightion',
    },
    codeRepository: 'https://github.com/rknightion/meraki-dashboard-ha',
    runtimePlatform: ['Home Assistant'],
    applicationSubCategory: [
      'Cisco Meraki',
      'Environmental Monitoring',
      'Network Monitoring',
      'Home Assistant Integration',
    ],
    offers: {
      '@type': 'Offer',
      price: '0',
      priceCurrency: 'USD',
    },
    screenshot: SITE.image,
    featureList: [
      'Fast MT sensor updates for Meraki environmental hardware',
      'Network performance metrics for MR and MS devices',
      'Per-device polling tuned for Meraki hardware',
      'Multi-organisation support with network grouping',
      'Native Home Assistant entities and services',
    ],
  };

  const docData = {
    '@context': 'https://schema.org',
    '@type': 'TechArticle',
    headline: document.title,
    description: document.querySelector('meta[name=\"description\"]')?.content || SITE.description,
    url: window.location.href,
    datePublished: document.querySelector('meta[name=\"date\"]')?.content,
    dateModified: document.querySelector('meta[name=\"git-revision-date-localized\"]')?.content,
    author: { '@type': 'Person', name: 'Rob Knighton' },
    publisher: { '@type': 'Organization', name: SITE.name, url: SITE.url },
    mainEntityOfPage: { '@type': 'WebPage', '@id': window.location.href },
    articleSection: getDocumentationSection(),
    keywords: getPageKeywords(),
    about: { '@type': 'SoftwareApplication', name: SITE.name },
  };

  addJsonLd(structuredData);
  addJsonLd(docData);
}

function addJsonLd(data) {
  const script = document.createElement('script');
  script.type = 'application/ld+json';
  script.textContent = JSON.stringify(data);
  document.head.appendChild(script);
}

function enhanceMetaTags() {
  if (!document.querySelector('meta[name=\"robots\"]')) {
    addMetaTag('name', 'robots', 'index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1');
  }

  addMetaTag('name', 'language', 'en');
  addMetaTag('http-equiv', 'Content-Type', 'text/html; charset=utf-8');

  const keywords = getPageKeywords();
  if (keywords) {
    addMetaTag('name', 'keywords', keywords);
  }

  if (isDocumentationPage()) {
    addMetaTag('name', 'article:tag', 'cisco-meraki');
    addMetaTag('name', 'article:tag', 'home-assistant');
    addMetaTag('name', 'article:tag', 'environmental-sensors');
    addMetaTag('name', 'article:tag', 'network-monitoring');
  }
}

function addOpenGraphTags() {
  const title = document.title || SITE.name;
  const description = document.querySelector('meta[name=\"description\"]')?.content || SITE.description;
  const url = window.location.href;

  addMetaTag('property', 'og:type', 'website');
  addMetaTag('property', 'og:site_name', SITE.name);
  addMetaTag('property', 'og:title', title);
  addMetaTag('property', 'og:description', description);
  addMetaTag('property', 'og:url', url);
  addMetaTag('property', 'og:locale', 'en_US');
  addMetaTag('property', 'og:image', SITE.image);
  addMetaTag('property', 'og:image:width', '1200');
  addMetaTag('property', 'og:image:height', '630');
  addMetaTag('property', 'og:image:alt', `${SITE.name} documentation social preview`);
}

function addTwitterCardTags() {
  const title = document.title || SITE.name;
  const description = document.querySelector('meta[name=\"description\"]')?.content || SITE.description;

  addMetaTag('name', 'twitter:card', 'summary_large_image');
  addMetaTag('name', 'twitter:title', title);
  addMetaTag('name', 'twitter:description', description);
  addMetaTag('name', 'twitter:image', SITE.image);
  addMetaTag('name', 'twitter:creator', SITE.twitter);
  addMetaTag('name', 'twitter:site', SITE.twitter);
}

function addCanonicalURL() {
  if (!document.querySelector('link[rel=\"canonical\"]')) {
    const canonical = document.createElement('link');
    canonical.rel = 'canonical';
    canonical.href = window.location.href;
    document.head.appendChild(canonical);
  }
}

function addMetaTag(attribute, name, content) {
  if (!document.querySelector(`meta[${attribute}=\"${name}\"]`)) {
    const meta = document.createElement('meta');
    meta.setAttribute(attribute, name);
    meta.content = content;
    document.head.appendChild(meta);
  }
}

function getDocumentationSection() {
  const path = window.location.pathname;
  if (path.includes('/getting-started')) return 'Getting Started';
  if (path.includes('/device-support')) return 'Device Support';
  if (path.includes('/supported-entities')) return 'Entities';
  if (path.includes('/development')) return 'Development';
  if (path.includes('/api-optimization')) return 'API Optimization';
  if (path.includes('/faq')) return 'FAQ';
  return 'Documentation';
}

function getPageKeywords() {
  const path = window.location.pathname;
  const content = document.body.textContent.toLowerCase();

  const keywords = ['meraki', 'home assistant', 'integration', 'sensors', 'network monitoring', 'cisco'];

  if (path.includes('/device-support')) keywords.push('device compatibility', 'hardware support');
  if (path.includes('/supported-entities')) keywords.push('entities', 'sensor entities', 'binary sensors');
  if (path.includes('/api-optimization')) keywords.push('api rate limits', 'polling intervals', 'performance');
  if (content.includes('mt1') || content.includes('mt15') || content.includes('mt40')) keywords.push('environmental sensors', 'mt series');
  if (content.includes('mr') || content.includes('ssid')) keywords.push('wireless', 'mr access points');
  if (content.includes('ms ')) keywords.push('switches', 'ms switches');

  return keywords.join(', ');
}

function isDocumentationPage() {
  return !window.location.pathname.endsWith('/') || window.location.pathname.includes('/docs/');
}
