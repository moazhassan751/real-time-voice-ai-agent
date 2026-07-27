import { test, expect } from '@playwright/test';

test.describe('Text Chat Interaction', () => {
  test('should send a text message and receive a response', async ({ page }) => {
    // Increase timeout for this test as the LLM might take a moment
    test.setTimeout(30000);

    await page.goto('/');

    const input = page.getByTestId('chat-input');
    const sendButton = page.getByTestId('send-button');

    // Send a message
    await input.fill('Hello');
    await sendButton.click();

    // Verify the user message appeared in the chat container
    const userMessage = page.getByTestId('chat-message-user').last();
    await expect(userMessage).toBeVisible();
    await expect(userMessage).toHaveText(/Hello/i);

    // Input should be empty and send button disabled while processing or after sending
    await expect(input).toHaveValue('');
    
    // Wait for the assistant's response to stream in
    const assistantMessage = page.getByTestId('chat-message-assistant').last();
    
    // Wait until the assistant message is visible and has some text length
    await expect(assistantMessage).toBeVisible({ timeout: 15000 });
    
    // Check that we got at least some text back
    await expect(async () => {
      const text = await assistantMessage.textContent();
      expect(text?.length).toBeGreaterThan(0);
    }).toPass({ timeout: 15000 });

    // Ensure the clear button appears once there are messages
    const clearButton = page.getByTestId('clear-button');
    await expect(clearButton).toBeVisible();

    // Click clear
    await clearButton.click();
    
    // Verify messages are cleared
    await expect(page.getByTestId('chat-message-user')).toHaveCount(0);
    await expect(page.getByTestId('chat-message-assistant')).toHaveCount(0);
    await expect(page.getByText('How can I help you?')).toBeVisible();
  });
});
