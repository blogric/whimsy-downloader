const express = require("express");
const axios = require("axios");
const cheerio = require("cheerio");

const app = express();
app.use(express.static("public"));

app.get("/download", async (req, res) => {
  try {
    let url = req.query.url;
    if (!url) return res.send("No URL provided");

    const response = await axios.get(url, { maxRedirects: 5 });
    const finalUrl = response.request.res.responseUrl;

    const htmlRes = await axios.get(finalUrl);
    const $ = cheerio.load(htmlRes.data);

    let videoUrl = $("video source").attr("src");

    if (!videoUrl) {
      videoUrl = $('meta[property="og:video"]').attr("content");
    }

    if (!videoUrl) {
      return res.send("Video not found");
    }

    res.json({
      success: true,
      video: videoUrl
    });

  } catch (err) {
    res.send("Error fetching video");
  }
});

app.listen(3000, () => console.log("Server running"));
