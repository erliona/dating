// Commitlint configuration for Conventional Commits
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    // Type rules
    'type-enum': [
      2,
      'always',
      [
        'feat',     // New feature
        'fix',      // Bug fix
        'docs',     // Documentation changes
        'style',    // Code style changes (formatting, etc.)
        'refactor', // Code refactoring
        'perf',     // Performance improvements
        'test',     // Adding or updating tests
        'build',    // Build system changes
        'ci',       // CI/CD changes
        'chore',    // Maintenance tasks
        'revert',   // Reverting changes
        'security', // Security improvements
        'deps',     // Dependency updates
        'config',   // Configuration changes
      ],
    ],
    
    // Scope rules
    'scope-enum': [
      2,
      'always',
      [
        'bot',           // Telegram bot
        'core',          // Core utilities
        'gateway',       // API Gateway
        'auth',          // Authentication service
        'profile',      // Profile service
        'discovery',     // Discovery service
        'media',         // Media service
        'chat',          // Chat service
        'admin',         // Admin service
        'notifications', // Notifications service
        'webapp',        // Frontend webapp
        'monitoring',    // Monitoring and observability
        'database',      // Database and migrations
        'docker',        // Docker configuration
        'ci',            // CI/CD
        'docs',          // Documentation
        'tests',         // Testing
        'security',      // Security
        'config',        // Configuration
        'deps',          // Dependencies
        'scripts',       // Scripts and automation
        'rules',         // Cursor AI rules
        'traefik',       // Traefik routing
        'jwt',           // JWT and authentication
        'migration',    // Database migrations
        'deployment',    // Deployment
        'monitoring',    // Monitoring
        'troubleshooting', // Troubleshooting
      ],
    ],
    
    // Subject rules
    'subject-case': [2, 'always', 'lower-case'],
    'subject-empty': [2, 'never'],
    'subject-full-stop': [2, 'never', '.'],
    'subject-max-length': [2, 'always', 100],
    'subject-min-length': [2, 'always', 10],
    
    // Header rules
    'header-max-length': [2, 'always', 100],
    'header-min-length': [2, 'always', 20],
    
    // Body rules
    'body-leading-blank': [2, 'always'],
    'body-max-line-length': [2, 'always', 100],
    
    // Footer rules
    'footer-leading-blank': [2, 'always'],
    'footer-max-line-length': [2, 'always', 100],
    
    // Type case
    'type-case': [2, 'always', 'lower-case'],
    'type-empty': [2, 'never'],
    
    // Scope case
    'scope-case': [2, 'always', 'lower-case'],
    
    // Examples of valid commits:
    // feat(auth): add JWT token refresh endpoint
    // fix(bot): resolve telegram webhook timeout issue
    // docs(api): update authentication documentation
    // style(core): format code with black
    // refactor(gateway): simplify routing logic
    // perf(database): optimize user query performance
    // test(auth): add unit tests for JWT validation
    // build(docker): update base image to python 3.11
    // ci(github): add static code analysis job
    // chore(deps): update aiohttp to latest version
    // revert(auth): revert JWT secret rotation
    // security(jwt): implement key rotation policy
    // deps(python): update requirements.txt
    // config(traefik): add middleware standards
  ],
  
  // Custom parser for breaking changes
  parserPreset: {
    parserOpts: {
      headerPattern: /^(\w*)(?:\(([^)]*)\))?: (.*)$/,
      headerCorrespondence: ['type', 'scope', 'subject'],
    },
  },
  
  // Help message for invalid commits
  helpUrl: 'https://github.com/conventional-changelog/commitlint/#what-is-commitlint',
};
