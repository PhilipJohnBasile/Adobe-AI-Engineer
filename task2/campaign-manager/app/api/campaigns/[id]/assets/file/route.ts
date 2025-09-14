import { NextRequest, NextResponse } from 'next/server';
import { readFile } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

// GET /api/campaigns/[id]/assets/file?path=filename
export async function GET(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const { searchParams } = new URL(request.url);
    const filePath = searchParams.get('path');
    const campaignId = params.id;

    if (!filePath) {
      return NextResponse.json({ error: 'File path is required' }, { status: 400 });
    }

    // Look for assets in the pipeline output directory (above the campaign-manager)
    const outputDir = path.join(process.cwd(), '..', 'output');
    
    if (!existsSync(outputDir)) {
      return NextResponse.json({ error: 'Output directory not found' }, { status: 404 });
    }

    // Determine the full file path
    let fullFilePath: string;
    
    // Check if it's a relative path (contains /) or just a filename
    if (filePath.includes('/')) {
      // It's a relative path like "product_dir/filename.png"
      fullFilePath = path.join(outputDir, filePath);
    } else {
      // It's just a filename, look in campaign-specific directory
      let campaignOutputDir = path.join(outputDir, campaignId);
      
      // Try with _001 suffix if exact match doesn't exist
      if (!existsSync(campaignOutputDir)) {
        campaignOutputDir = path.join(outputDir, `${campaignId}_001`);
      }
      
      if (existsSync(campaignOutputDir)) {
        fullFilePath = path.join(campaignOutputDir, filePath);
      } else {
        // Fallback to looking in root output directory
        fullFilePath = path.join(outputDir, filePath);
      }
    }

    // Security check: ensure the path is within the output directory
    const resolvedPath = path.resolve(fullFilePath);
    const resolvedOutputDir = path.resolve(outputDir);
    
    if (!resolvedPath.startsWith(resolvedOutputDir)) {
      return NextResponse.json({ error: 'Invalid file path' }, { status: 403 });
    }

    if (!existsSync(fullFilePath)) {
      return NextResponse.json({ error: 'File not found' }, { status: 404 });
    }

    // Read the file
    const fileBuffer = await readFile(fullFilePath);
    
    // Determine content type based on file extension
    const ext = path.extname(fullFilePath).toLowerCase();
    let contentType = 'application/octet-stream';
    
    switch (ext) {
      case '.png':
        contentType = 'image/png';
        break;
      case '.jpg':
      case '.jpeg':
        contentType = 'image/jpeg';
        break;
      case '.svg':
        contentType = 'image/svg+xml';
        break;
      case '.webp':
        contentType = 'image/webp';
        break;
      case '.gif':
        contentType = 'image/gif';
        break;
    }

    // Return the file with appropriate headers
    return new NextResponse(fileBuffer, {
      status: 200,
      headers: {
        'Content-Type': contentType,
        'Cache-Control': 'public, max-age=86400', // Cache for 1 day
        'Content-Disposition': `inline; filename="${path.basename(fullFilePath)}"`,
      },
    });

  } catch (error) {
    console.error('Error serving asset file:', error);
    return NextResponse.json(
      { error: 'Failed to serve asset file' }, 
      { status: 500 }
    );
  }
}