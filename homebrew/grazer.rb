class Grazer < Formula
  desc "Multi-platform content discovery for AI agents"
  homepage "https://github.com/Scottcjn/grazer-skill"
  url "https://registry.npmjs.org/grazer-skill/-/grazer-skill-1.1.0.tgz"
  license "MIT"

  depends_on "node"

  def install
    system "npm", "install", *std_npm_args
    bin.install_symlink Dir["#{libexec}/bin/*"]
  end

  test do
    assert_match "1.1.0", shell_output("#{bin}/grazer --version")
  end
end
