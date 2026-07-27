import { test, expect } from '@playwright/test';

test.describe('Voice Interaction', () => {
  test('should start and stop recording, then send audio to backend', async ({ page }) => {
    // Note: Due to fake audio capture we don't know exactly what will be transcribed,
    // (it'll be silence), so we just test the UI states.
    test.setTimeout(30000);
    
    await page.goto('/');

    const micButton = page.getByTestId('mic-button');

    // Click to start recording
    await micButton.click();

    // Wait a brief moment to allow recording to capture some data
    await page.waitForTimeout(1000);

    // The UI should show "Recording... tap to stop"
    await expect(page.getByText('Recording… tap to stop')).toBeVisible();

    // Input and Send button should be disabled during recording
    const input = page.getByTestId('chat-input');
    await expect(input).toBeDisabled();

    // Click mic again to stop recording
    await micButton.click();

    // The UI should show processing dots while it communicates with backend
    // Or at least it should no longer show the recording text
    await expect(page.getByText('Recording… tap to stop')).toBeHidden();

    // Wait for either the user message (if transcription success) or error alert (if transcription fails due to silence)
    // Since our test audio is absolute silence, whisper might fail to transcribe and return nothing.
    // The UI handles this by showing an alert or doing nothing if the backend returns nothing.
    // We'll just verify the UI returns to a ready state eventually.
    
    await expect(input).toBeEnabled({ timeout: 15000 });
  });
});
