from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from sportstats.services.model_assets import download_model, ensure_model_file


class FakeResponse(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc, _traceback):
        return False


class ModelAssetsTest(unittest.TestCase):
    def test_download_model_writes_destination(self):
        with TemporaryDirectory() as directory:
            output_path = Path(directory) / "models" / "best.pt"

            with patch("sportstats.services.model_assets.urlopen", return_value=FakeResponse(b"weights")) as urlopen:
                result = download_model("https://example.com/best.pt", output_path)

            self.assertEqual(result, output_path)
            self.assertEqual(output_path.read_bytes(), b"weights")
            urlopen.assert_called_once_with("https://example.com/best.pt", timeout=120)

    def test_ensure_model_file_skips_download_when_file_exists(self):
        with TemporaryDirectory() as directory:
            output_path = Path(directory) / "best.pt"
            output_path.write_bytes(b"existing")

            with patch("sportstats.services.model_assets.urlopen") as urlopen:
                result = ensure_model_file(output_path, "https://example.com/best.pt")

            self.assertEqual(result, output_path)
            self.assertEqual(output_path.read_bytes(), b"existing")
            urlopen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
