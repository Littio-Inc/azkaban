-- Add role column to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'user' NOT NULL;

-- Create index for role
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Set mauricio.quinche@littio.co as admin
-- First, we need to find the user by email and update their role
-- Note: This assumes the user already exists. If not, they will be created as admin on first login
UPDATE users SET role = 'admin', is_active = true WHERE email = 'mauricio.quinche@littio.co';

