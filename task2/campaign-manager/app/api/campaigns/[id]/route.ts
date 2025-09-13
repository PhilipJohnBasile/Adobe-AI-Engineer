import { NextResponse } from "next/server";
import { readCampaign, writeCampaign } from "@/lib/campaignFs";
import { CampaignSchema } from "@/lib/campaignSchema";

export async function GET(_: Request, { params }: { params: { id: string } }) {
  try {
    const data = await readCampaign(params.id);
    return NextResponse.json(data);
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 404 });
  }
}

export async function PUT(req: Request, { params }: { params: { id: string } }) {
  try {
    const body = await req.json();
    const parsed = CampaignSchema.parse(body);
    await writeCampaign(params.id, parsed);
    return NextResponse.json({ ok: true });
  } catch (e: any) {
    if (e?.issues) return NextResponse.json({ errors: e.issues }, { status: 400 });
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}