class Grazer < Formula
  desc "Multi-platform content discovery for AI agents"
  homepage "https://github.com/Scottcjn/grazer-skill"
  url "https://registry.npmjs.org/grazer-skill/-/grazer-skill-1.7.0.tgz"
  sha256 "6329e4affe490f14526a95d9b52be5b1f379be31b034cfafffcc667e807e2b98"
  license "MIT"

  depends_on "node"

  def install
    system "npm", "install", *std_npm_args
    bin.install_symlink Dir["#{libexec}/bin/*"]
  end

  test do
    assert_match "1.7.0", shell_output("#{bin}/grazer --version")
  end
end
