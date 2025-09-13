import { NextResponse } from "next/server";
import { writeCampaign } from "@/lib/campaignFs";
import { CampaignSchema } from "@/lib/campaignSchema";

export async function POST(req: Request, { params }: { params: { id: string } }) {
  try {
    const form = await req.formData();
    const file = form.get("file") as File | null;
    if (!file) return NextResponse.json({ error: "file missing" }, { status: 400 });
    const text = await file.text();
    const parsed = CampaignSchema.parse(JSON.parse(text));
    await writeCampaign(params.id, parsed);
    return NextResponse.json({ ok: true });
  } catch (e: any) {
    if (e?.issues) return NextResponse.json({ errors: e.issues }, { status: 400 });
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
