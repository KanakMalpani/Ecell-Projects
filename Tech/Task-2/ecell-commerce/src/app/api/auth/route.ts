import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/prisma";
import { hashPassword, signToken, TOKEN_COOKIE, verifyPassword } from "@/lib/auth";

const registerSchema = z.object({
  name: z.string().min(2),
  email: z.string().email(),
  password: z.string().min(6),
});

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const data = registerSchema.parse(body);

    const existing = await prisma.user.findUnique({ where: { email: data.email } });
    if (existing) {
      return NextResponse.json({ error: "Email already registered" }, { status: 400 });
    }

    const hashed = await hashPassword(data.password);
    const user = await prisma.user.create({
      data: {
        name: data.name,
        email: data.email,
        password: hashed,
        role: "USER",
      },
    });

    const token = signToken({
      id: user.id,
      email: user.email,
      name: user.name,
      role: user.role,
    });

    const response = NextResponse.json({
      user: { id: user.id, email: user.email, name: user.name, role: user.role },
    });

    response.cookies.set(TOKEN_COOKIE, token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 60 * 60 * 24 * 7,
      path: "/",
    });

    return response;
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json({ error: error.issues[0]?.message }, { status: 400 });
    }
    return NextResponse.json({ error: "Registration failed" }, { status: 500 });
  }
}

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
});

export async function PUT(request: NextRequest) {
  try {
    const body = await request.json();
    const data = loginSchema.parse(body);

    const user = await prisma.user.findUnique({ where: { email: data.email } });
    if (!user || !(await verifyPassword(data.password, user.password))) {
      return NextResponse.json({ error: "Invalid email or password" }, { status: 401 });
    }

    const token = signToken({
      id: user.id,
      email: user.email,
      name: user.name,
      role: user.role,
    });

    const response = NextResponse.json({
      user: { id: user.id, email: user.email, name: user.name, role: user.role },
    });

    response.cookies.set(TOKEN_COOKIE, token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 60 * 60 * 24 * 7,
      path: "/",
    });

    return response;
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json({ error: error.issues[0]?.message }, { status: 400 });
    }
    return NextResponse.json({ error: "Login failed" }, { status: 500 });
  }
}

export async function DELETE() {
  const response = NextResponse.json({ success: true });
  response.cookies.set(TOKEN_COOKIE, "", { httpOnly: true, maxAge: 0, path: "/" });
  return response;
}
