"""
Tests for BoTTube Integration - #83
"""
import pytest
from bottube_integration import BoTTubeIntegration

class TestBoTTubeIntegration:
    def test_init(self):
        integration = BoTTubeIntegration()
        assert integration.name == "BoTTube Integration"
    
    def test_get_trending(self):
        integration = BoTTubeIntegration()
        trending = integration.get_trending()
        assert len(trending) > 0
    
    def test_get_stats(self):
        integration = BoTTubeIntegration()
        stats = integration.get_stats()
        assert "total_videos" in stats

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
