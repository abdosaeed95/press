const purgecss = require('@fullhuman/postcss-purgecss')({
	content: ['./public/index.html', './src/**/*.html', './src/**/*.vue'],
    defaultExtractor: content => content.match(/[\w-/:]+(?<!:)/g) || [],
    whitelistPatternsChildren: [/chart-container$/, /graph-svg-tip$/]
});

module.exports = {
	plugins: [
		require('tailwindcss'),
		require('autoprefixer'),
		process.env.NODE_ENV === 'production' ? purgecss : null
	].filter(Boolean)
};
