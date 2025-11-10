import discord
import os
from huggingface_hub import InferenceClient

# === CONFIGURATION ===
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')  # Your Discord bot token
HF_TOKEN = os.getenv('HF_TOKEN')  # Your Hugging Face token

# System prompt for ethical hacking context
SYSTEM_PROMPT = """You are DeepHat, an ethical hacking and cybersecurity assistant. Your purpose is to help users learn about:
- Vulnerability analysis and identification
- Secure coding practices
- Penetration testing concepts
- Red/blue team strategies
- Threat modeling
- Security best practices

Always emphasize ethical and legal use of security knowledge. Provide educational content only."""

# Conversation history (stored per channel)
conversation_history = {}

# === HUGGING FACE SETUP ===
client_hf = InferenceClient(
    api_key=HF_TOKEN
)

# === DISCORD SETUP ===
intents = discord.Intents.default()
intents.message_content = True  # Required for reading message content
intents.guilds = True          # Required for basic bot functionality
intents.guild_messages = True  # Required for message events
client = discord.Client(intents=intents)

# === AI Query Function ===
def ask_deephat(prompt, channel_id):
    """Send a prompt to DeepHat and get a response with conversation context."""
    try:
        # Initialize conversation history for this channel if needed
        if channel_id not in conversation_history:
            conversation_history[channel_id] = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]
        
        # Add user message to history
        conversation_history[channel_id].append({
            "role": "user",
            "content": prompt
        })
        
        # Keep only last 10 messages (5 exchanges) to avoid token limits
        if len(conversation_history[channel_id]) > 11:  # 1 system + 10 messages
            conversation_history[channel_id] = [conversation_history[channel_id][0]] + conversation_history[channel_id][-10:]
        
        # Get response from DeepHat
        completion = client_hf.chat.completions.create(
            model="DeepHat/DeepHat-V1-7B:featherless-ai",
            messages=conversation_history[channel_id],
            max_tokens=1000,
            temperature=0.7
        )
        
        response = completion.choices[0].message.content
        
        # Add assistant response to history
        conversation_history[channel_id].append({
            "role": "assistant",
            "content": response
        })
        
        return response
        
    except Exception as e:
        print(f"🔥 Error querying DeepHat: {e}")
        return "Sorry, I encountered an error. Please try again later."

# === Bot Events ===
@client.event
async def on_ready():
    print(f"✅ DeepHat Bot is online as {client.user}")
    print(f"🔒 Ready to help with ethical hacking education!")

@client.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == client.user:
        return
    
    # Only respond when mentioned
    if client.user in message.mentions:
        # Extract the actual prompt (remove bot mention)
        prompt = message.content.replace(f"<@{client.user.id}>", "").strip()
        
        if not prompt:
            await message.channel.send(
                "👋 Hello! I'm DeepHat, your ethical hacking assistant. "
                "Ask me about:\n"
                "• Security vulnerabilities\n"
                "• Code review\n"
                "• Penetration testing\n"
                "• Secure coding practices\n"
                "• Threat analysis\n\n"
                "**Example:** `@DeepHat analyze this SQL query for vulnerabilities`"
            )
            return
        
        # Special command: clear conversation history
        if prompt.lower() in ["clear", "reset", "new conversation"]:
            if message.channel.id in conversation_history:
                del conversation_history[message.channel.id]
            await message.channel.send("🔄 Conversation history cleared. Starting fresh!")
            return
        
        # Show typing indicator while processing
        async with message.channel.typing():
            reply = ask_deephat(prompt, message.channel.id)
            
            # Discord has a 2000 character limit, split if needed
            if len(reply) > 2000:
                chunks = [reply[i:i+1900] for i in range(0, len(reply), 1900)]
                for chunk in chunks:
                    await message.channel.send(chunk)
            else:
                await message.channel.send(reply)

# === Run Bot ===
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ Error: DISCORD_TOKEN environment variable not set!")
        exit(1)
    if not HF_TOKEN:
        print("❌ Error: HF_TOKEN environment variable not set!")
        exit(1)
    
    client.run(DISCORD_TOKEN)