import {test,expect,type Page} from "@playwright/test";
import {readFileSync} from "node:fs";

const url=process.env.CASE_FLOW_URL || "http://127.0.0.1:4199/client/case-flow.html";
const run="17lands-trajectories-20260909-01";
const artifact=(id:string)=>readFileSync(new URL("../../replays/"+run+"/artifacts/"+id,import.meta.url),"utf8");
const replay=readFileSync(new URL("../../replays/"+run+"/replay.json",import.meta.url),"utf8");
test.use({launchOptions:{args:["--js-flags=--max-old-space-size=1536"]}});
async function mount(page:Page,corrupt=false){
  await page.route("**/factory-api/**",route=>{
    const pathname=new URL(route.request().url()).pathname;
    if(pathname.endsWith("/replay.json"))return route.fulfill({contentType:"application/json",body:replay});
    const id=pathname.split("/").pop() || "";
    if(/^[a-f0-9]{64}$/.test(id))return route.fulfill({contentType:"application/json",body:artifact(id)+(corrupt?" ":"")});
    return route.abort();
  });
  await page.goto(url);
}
test("the recording stays separate from the engine's hypothetical cards and later snapshots",async({page})=>{
  const errors:string[]=[];page.on("pageerror",e=>errors.push(e.message));
  await mount(page);
  await expect(page.locator(".stage-heading")).toContainText("recorded game");
  const observed=page.locator('[data-board="recorded"]');
  await expect(observed.locator(".unknown-hand")).toContainText("7 cards");
  await expect(observed.locator('[data-card="Forest"]')).toHaveCount(0);
  await page.locator('#outline [data-step="1"]').click();
  await expect(page.locator('[data-board="engine"] .board-topline')).toContainText("End");
  await page.locator('#outline [data-step="2"]').click();
  let engine=page.locator('[data-board="engine"]');
  await expect(engine).toContainText("Hand · 8 cards");
  await expect(engine.locator('[data-card="Forest"]')).toHaveCount(1);
  await page.getByRole("button",{name:"Step through discard"}).click();
  engine=page.locator('[data-board="engine"]');
  await expect(engine).toContainText("Hand · 7 cards");
  await expect(engine).toContainText("Graveyard · 1 card");
  await expect(engine).toContainText("next draw has not happened");
  await expect(engine.locator(".zone").filter({hasText:"Graveyard"}).locator('[data-card="Forest"]')).toHaveCount(1);
  await expect(observed.locator(".unknown-hand")).toContainText("7 cards");
  await expect(observed.locator('[data-card="Island"]')).toHaveCount(1);
  await page.locator('#outline [data-step="5"]').click();
  await expect(page.locator(".stage-heading")).toContainText("still blocked");
  await expect(page.locator("#detail")).toContainText("Unchanged");
  expect(errors).toEqual([]);
});
test("cards stay inspectable when external images fail, on a narrow viewport",async({page})=>{
  await page.setViewportSize({width:390,height:844});
  await page.route("https://cards.scryfall.io/**",route=>route.abort());
  await mount(page);
  await expect(page.locator(".stage-heading")).toBeVisible();
  const island=page.locator('[data-board="recorded"] [data-card="Island"]');
  await expect(island.locator(".card-fallback")).toBeVisible();
  await island.click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(page.locator("#dialog-card-name")).toHaveText("Island");
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toBeHidden();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
});
test("tampered evidence cannot produce a visual game state",async({page})=>{
  await mount(page,true);
  await expect(page.locator("#error")).toContainText("do not match");
  await expect(page.locator('[data-board]')).toHaveCount(0);
  for(const id of ["play","previous","next","restart","progress"])await expect(page.locator("#"+id)).toBeDisabled();
});
