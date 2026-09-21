class Grazer < Formula
  desc "Multi-platform content discovery for AI agents — 24 platforms including Bluesky, Farcaster, Mastodon, Nostr"
  homepage "https://github.com/Scottcjn/grazer-skill"
  url "https://registry.npmjs.org/grazer-skill/-/grazer-skill-2.0.1.tgz"
  license "MIT"

  depends_on "node"

  def install
    system "npm", "install", *std_npm_args
    bin.install_symlink Dir["#{libexec}/bin/*"]
  end

  test do
    assert_match "2.0.1", shell_output("#{bin}/grazer --version")
  end
end
