import pytest
from unittest.mock import patch, MagicMock
from keychange.cli import main

@pytest.mark.vst
@pytest.mark.integration
def test_cli_vst_list_params(mock_vst3, test_vst_path, capsys):
    # Test listing VST parameters
    with patch('sys.argv', ['keychange', '--vst', str(test_vst_path), '--list-vst-params']):
        main()
        
    captured = capsys.readouterr()
    assert "VST Plugin Parameters" in captured.out
    assert "gain" in captured.out
    assert "mix" in captured.out
    assert "bypass" in captured.out

def test_cli_vst_missing_plugin(capsys):
    with patch('sys.argv', ['keychange', '--vst', 'nonexistent.vst3']):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code != 0
    
    captured = capsys.readouterr()
    assert "Error" in captured.err
    assert "not found" in captured.err

def test_cli_vst_invalid_param(mock_vst3, tmp_path, capsys):
    vst_path = tmp_path / "test.vst3"
    vst_path.touch()
    
    # Test invalid parameter name
    with patch('sys.argv', ['keychange', '--vst', str(vst_path), '--vst-param', 'invalid', '0.5']):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code != 0
    
    # Test invalid parameter value
    with patch('sys.argv', ['keychange', '--vst', str(vst_path), '--vst-param', 'gain', '1.5']):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code != 0

def test_cli_vst_stream(mock_vst3, mock_sounddevice, tmp_path):
    vst_path = tmp_path / "test.vst3"
    vst_path.touch()
    
    # Mock streaming to run for a short time
    def mock_sleep(seconds):
        raise KeyboardInterrupt
    
    with patch('time.sleep', side_effect=mock_sleep):
        with patch('sys.argv', [
            'keychange',
            '--vst', str(vst_path),
            '--vst-param', 'gain', '0.5',
            '--duration', '30'
        ]):
            # Mock sounddevice stream
            mock_stream = MagicMock()
            mock_sounddevice.InputStream.return_value = mock_stream
            
            main()
            
            # Verify stream was started and stopped
            assert mock_stream.start.called
            assert mock_stream.stop.called
            assert mock_stream.close.called

def test_cli_vst_list_params_no_vst(capsys):
    # Test --list-vst-params without --vst
    with patch('sys.argv', ['keychange', '--list-vst-params']):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code != 0
    
    captured = capsys.readouterr()
    assert "Error" in captured.err
    assert "--list-vst-params requires --vst" in captured.err

def test_cli_vst_with_device(mock_vst3, mock_sounddevice, tmp_path):
    vst_path = tmp_path / "test.vst3"
    vst_path.touch()
    
    # Test VST with specific audio device
    def mock_sleep(seconds):
        raise KeyboardInterrupt
    
    with patch('time.sleep', side_effect=mock_sleep):
        with patch('sys.argv', [
            'keychange',
            '--vst', str(vst_path),
            '--device', 'Test Device',
            '--duration', '30'
        ]):
            mock_stream = MagicMock()
            mock_sounddevice.InputStream.return_value = mock_stream
            
            main()
            
            # Verify device was used
            call_args = mock_sounddevice.InputStream.call_args[1]
            assert call_args['device'] == 'Test Device'
