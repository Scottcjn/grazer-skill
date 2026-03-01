class Grazer < Formula
  desc "Multi-platform content discovery for AI agents"
  homepage "https://github.com/Scottcjn/grazer-skill"
  url "https://registry.npmjs.org/grazer-skill/-/grazer-skill-1.8.0.tgz"
  sha256 "bb52439d95dbff057bd2bd20ddf695c75a04f99c262e743985b61604bab5c42d"
  license "MIT"

  depends_on "node"

  def install
    system "npm", "install", *std_npm_args
    bin.install_symlink Dir["#{libexec}/bin/*"]
  end

  test do
    assert_match "1.8.0", shell_output("#{bin}/grazer --version")
  end
end
