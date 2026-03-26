class Grazer < Formula
  desc "Multi-platform content discovery for AI agents — 24 platforms including Bluesky, Farcaster, Mastodon, Nostr"
  homepage "https://github.com/Scottcjn/grazer-skill"
  url "https://registry.npmjs.org/grazer-skill/-/grazer-skill-2.0.0.tgz"
  sha256 "0a755b5cb932cf4df28c4cabd1d7736840ba3906a7f4da3f6e37b2e27f23112a"
  license "MIT"

  depends_on "node"

  def install
    system "npm", "install", *std_npm_args
    bin.install_symlink Dir["#{libexec}/bin/*"]
  end

  test do
    assert_match "2.0.0", shell_output("#{bin}/grazer --version")
  end
end
