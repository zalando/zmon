module.exports = function(grunt) {
    grunt.initConfig({
        watch: {
            main: {
                files: ['./js/**/**.js', './templates/**', './views/**', './test/e2e/**/*.js'],
                tasks: ['shell:protractor'],
                options: {
                    interrupt: true
                }
            }
        },

        shell: {
            protractor: {
                options: {
                    stdout: true,
                    stderr: true,
                    error: true
                },
                command: './node_modules/protractor/bin/protractor ./test/protractor.config.js'
            },
            karma: {
                options: {
                    stdout: true,
                    stderr: true,
                    error: true
                },
                command: './node_modules/karma/bin/karma start ./test/karma.config.js'
            },
            init: {
                options: {
                    stdout: true,
                    stderr: true,
                    error: true
                },
                command: './node_modules/protractor/bin/webdriver-manager update --standalone && ./node_modules/protractor/bin/webdriver-manager start'
            },
            'jenkins-e2e': {
                options: {
                    stdout: true,
                    stderr: true,
                    error: true
                },
                command: './node_modules/protractor/bin/protractor ./test/jenkins-protractor.config.js'
            },
            'jenkins-unit': {
                options: {
                    stdout: true,
                    stderr: true,
                    error: true
                },
                command: './node_modules/karma/bin/karma start ./test/jenkins-karma.config.js'
            },
            'smoke-e2e': {
                options: {
                    stdout: true,
                    stderr: true,
                    error: true
                },
                command: './node_modules/protractor/bin/protractor ./test/smoke-protractor.config.js'
            }
        }
    });

    grunt.loadNpmTasks('grunt-contrib-watch');
    grunt.loadNpmTasks('grunt-shell');

    grunt.registerTask('init', ['shell:init']);
    grunt.registerTask('run-e2e', ['shell:protractor']);
    grunt.registerTask('run-unit', ['shell:karma']);
    grunt.registerTask('jenkins-e2e', ['shell:jenkins-e2e']);
    grunt.registerTask('jenkins-unit', ['shell:jenkins-unit']);
    grunt.registerTask('smoke-e2e', ['shell:smoke-e2e']);
};