"""Exercise the real checker function without running room startup or services."""
import pathlib
import subprocess
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / 'bin/codex-ensure-standalone'

class MCPCommands(unittest.TestCase):
    def check_config(self, config):
        source = SCRIPT.read_text()
        function = source.split('check_mcp_config_commands() {', 1)[1].split('\ncheck_room_files()', 1)[0]
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / 'config.toml'
            path.write_text(config)
            result = subprocess.run(['bash', '-c', '''
CONFIG="$1"
pass() { echo "PASS $*"; }
fail() { echo "FAIL $*"; }
warn() { echo "WARN $*"; }
check_mcp_config_commands() {''' + function + '\ncheck_mcp_config_commands', 'test', str(path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_disabled_order_and_quoted_name(self):
        output = self.check_config('''[mcp_servers."disabled.one"]
command = '/definitely-missing-mcp'
[ mcp_servers."disabled.one".env ]
EXAMPLE = 'not a command'
[mcp_servers."disabled.one"]
''')
        self.assertIn('FAIL Cannot parse', output)  # duplicate tables must fail closed
        for body in ("enabled = false\ncommand = '/definitely-missing-mcp'", "command = '/definitely-missing-mcp'\nenabled = false # disabled"):
            output = self.check_config('[mcp_servers."disabled.one"]\n' + body)
            self.assertIn('skipped for disabled server: disabled.one', output)
            self.assertNotIn('FAIL', output)

    def test_enabled_and_default_enabled_missing(self):
        for enabled in ('enabled = true\n', ''):
            for command in ('/definitely-missing-mcp', 'definitely-missing-mcp'):
                output = self.check_config('[mcp_servers.active]\n' + enabled + 'command = "' + command + '"')
                self.assertIn('FAIL MCP command', output)

    def test_valid_and_relative(self):
        self.assertNotIn('FAIL', self.check_config('[mcp_servers.ok]\ncommand = "/bin/sh"'))
        self.assertIn('configured cwd', self.check_config('[mcp_servers.ok]\ncommand = "./sh"\ncwd = "/bin"'))
        self.assertIn('WARN', self.check_config('[mcp_servers.relative]\ncommand = "./missing"'))

    def test_empty_http_and_invalid(self):
        for config in ('', '[mcp_servers.http]\nurl = "https://example.invalid"'):
            self.assertNotIn('FAIL', self.check_config(config))
        for config in ('[broken', '[mcp_servers.bad]\nenabled = "false"', '[mcp_servers.bad]\ncommand = 1'):
            self.assertIn('FAIL Cannot parse', self.check_config(config))

if __name__ == '__main__':
    unittest.main()
