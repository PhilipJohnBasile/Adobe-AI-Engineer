import { NextResponse } from "next/server";
import { readCampaign } from "@/lib/campaignFs";

export async function GET(_: Request, { params }: { params: { id: string } }) {
  try {
    const data = await readCampaign(params.id);
    const file = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    return new NextResponse(file, {
      headers: {
        "Content-Disposition": `attachment; filename="${params.id}.json"`,
        "Content-Type": "application/json"
      }
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 404 });
  }
}
