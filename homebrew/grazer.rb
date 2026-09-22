class Grazer < Formula
  desc "Multi-platform content discovery for AI agents — 24 platforms including Bluesky, Farcaster, Mastodon, Nostr"
  homepage "https://github.com/Scottcjn/grazer-skill"
  url "https://registry.npmjs.org/grazer-skill/-/grazer-skill-2.0.1.tgz"
  sha256 "b5a71f50230d4ca35a390382a1cdbd81f50b01e7fd4614b8ef4843728a8c2d91"
  license "MIT"

  depends_on "node"

  def install
    system "npm", "install", *std_npm_args
    bin.install_symlink Dir["#{libexec}/bin/*"]
  end

  test do
    # The published CLI's --version string lags the package version
    # (src/cli.ts hardcodes it), so test that the binary runs rather than
    # asserting an exact version.
    assert_match "discover", shell_output("#{bin}/grazer --help")
  end
end
